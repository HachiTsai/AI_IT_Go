import json
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import google_news_digest as gnd

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google 新聞</title>
    <item>
      <title>台積電公布最新季報 營收創新高 - 經濟日報</title>
      <link>https://news.google.com/rss/articles/1</link>
      <pubDate>Thu, 26 Nov 2026 04:00:00 GMT</pubDate>
      <source url="https://money.udn.com">經濟日報</source>
    </item>
    <item>
      <title>台積電公布最新季報 營收再創新高！ - 工商時報</title>
      <link>https://news.google.com/rss/articles/2</link>
      <pubDate>Thu, 26 Nov 2026 03:30:00 GMT</pubDate>
      <source url="https://www.ctee.com.tw">工商時報</source>
    </item>
    <item>
      <title>AI 伺服器需求強勁 供應鏈受惠 - 中央社</title>
      <link>https://news.google.com/rss/articles/3</link>
      <pubDate>Mon, 23 Nov 2026 01:00:00 GMT</pubDate>
      <source url="https://www.cna.com.tw">中央社</source>
    </item>
  </channel>
</rss>
"""


class TestGoogleNewsDigest(unittest.TestCase):
    def test_build_rss_url(self):
        self.assertEqual(
            gnd.build_rss_url("tw"),
            "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        )
        self.assertEqual(
            gnd.build_rss_url("US", query="TSMC AI"),
            "https://news.google.com/rss/search?q=TSMC+AI&hl=en-US&gl=US&ceid=US%3Aen",
        )
        with self.assertRaises(ValueError):
            gnd.build_rss_url("XX")

    def test_parse_and_dedupe(self):
        articles = gnd.parse_rss_xml(SAMPLE_RSS, region="tw")
        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0].title, "台積電公布最新季報 營收創新高")
        self.assertEqual(articles[0].source, "經濟日報")

        deduped = gnd.dedupe_articles(articles)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0].related_sources, ["工商時報"])

    def test_filter_by_hours(self):
        articles = gnd.parse_rss_xml(SAMPLE_RSS, region="TW")
        now = datetime(2026, 11, 26, 5, 0, tzinfo=UTC)
        recent = gnd.filter_by_hours(articles, hours=24, now=now)
        self.assertEqual(len(recent), 2)
        self.assertTrue(all(a.published_at and a.published_at >= now - timedelta(hours=24) for a in recent))

    def test_main_json_output(self):
        with patch.object(gnd, "fetch_rss", return_value=SAMPLE_RSS):
            with patch("builtins.print") as mock_print:
                rc = gnd.main(["--regions", "TW", "--hours", "0", "--format", "json"])
        self.assertEqual(rc, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["region"], "TW")
        self.assertEqual(payload[0]["related_sources"], ["工商時報"])

    def test_extract_paragraphs(self):
        sample_html = (
            "<html><body><nav><p>導覽列應該被略過而且這段超過二十個字元也不該出現</p></nav>"
            "<article><p>這是第一段新聞正文，內容夠長應該被保留下來。</p>"
            "<p>太短</p>"
            "<p>這是第二段新聞正文，包含更多技術細節與市場分析。</p></article></body></html>"
        )
        extracted = gnd.extract_paragraphs(sample_html, max_chars=200)
        self.assertIn("這是第一段新聞正文", extracted)
        self.assertIn("這是第二段新聞正文", extracted)
        self.assertNotIn("導覽列", extracted)
        self.assertNotIn("太短", extracted)

    def test_main_analyze_mode(self):
        usage = {"promptTokenCount": 1000, "candidatesTokenCount": 500, "thoughtsTokenCount": 200}
        with (
            patch.object(gnd, "fetch_rss", return_value=SAMPLE_RSS),
            patch.object(gnd, "enrich_articles") as mock_enrich,
            patch.object(gnd, "analyze_with_gemini", return_value=("## 模擬簡報", usage)) as mock_gemini,
            patch("builtins.print") as mock_print,
        ):
            rc = gnd.main(["-q", "AI", "-r", "TW", "--hours", "0", "--analyze", "--model", "gemini-2.5-pro"])
        self.assertEqual(rc, 0)
        mock_enrich.assert_called_once()
        mock_gemini.assert_called_once()
        printed = mock_print.call_args.args[0]
        self.assertIn("## 模擬簡報", printed)
        self.assertIn("gemini-2.5-pro", printed)

    def test_resolve_perspective(self):
        self.assertIn("投資人", gnd.resolve_perspective("investor"))
        self.assertEqual(gnd.resolve_perspective("台灣雲端維運工程師"), "台灣雲端維運工程師")
        self.assertIn("情報分析師", gnd.resolve_perspective(None))


if __name__ == "__main__":
    unittest.main()
