import json
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

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

SAMPLE_DATA_P = (
    '%.@.[["en-US","US"],null],"CBMiT0FVX3lxTE5oamY4",1,2,null,false,1795673336,"AdwtSYOadUX1qYZpyLLC3ct8aXML"]'
)
SAMPLE_REDIRECT_HTML = f'<c-wiz data-p="{SAMPLE_DATA_P.replace(chr(34), "&quot;")}"></c-wiz>'
SAMPLE_BATCH_TEXT = ')]}\'\n\n[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"https://www.reuters.com/tech/ai-story\\",1]",null,null,null,"generic"]]'


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

    def test_is_blocked_domain(self):
        self.assertTrue(gnd.is_blocked_domain("https://www.reuters.com/world/ai"))
        self.assertTrue(gnd.is_blocked_domain("https://tw.stock.yahoo.com/news/abc"))
        self.assertTrue(gnd.is_blocked_domain("https://finance.yahoo.com/news/abc"))
        self.assertTrue(gnd.is_blocked_domain("https://www.cnbc.com/2026/11/26/ai.html"))
        self.assertFalse(gnd.is_blocked_domain("https://udn.com/news/story/6811/9903707"))

    def test_decode_data_p_and_resolve_success(self):
        article_id, ts, sig = gnd.decode_data_p_params(SAMPLE_REDIRECT_HTML)
        self.assertEqual(article_id, "CBMiT0FVX3lxTE5oamY4")
        self.assertEqual(ts, 1795673336)
        self.assertEqual(sig, "AdwtSYOadUX1qYZpyLLC3ct8aXML")

        get_resp = MagicMock(status_code=200, text=SAMPLE_REDIRECT_HTML)
        post_resp = MagicMock(status_code=200, text=SAMPLE_BATCH_TEXT)
        client = MagicMock()
        client.request.side_effect = [get_resp, post_resp]

        resolved_url, ok, err = gnd.resolve_google_news_url("https://news.google.com/rss/articles/1", client)
        self.assertTrue(ok)
        self.assertIsNone(err)
        self.assertEqual(resolved_url, "https://www.reuters.com/tech/ai-story")

    def test_resolve_failure_does_not_return_original_url(self):
        bad_resp = MagicMock(status_code=200, text="<html>no data-p</html>")
        client = MagicMock()
        client.request.return_value = bad_resp

        resolved_url, ok, err = gnd.resolve_google_news_url("https://news.google.com/rss/articles/1", client)
        self.assertFalse(ok)
        self.assertIsNone(resolved_url)
        self.assertIn("data-p", err or "")

    def test_collect_news_partial_region_failure(self):
        def fake_fetch(url: str) -> str:
            if "TW" in url:
                raise RuntimeError("HTTP 429")
            return SAMPLE_RSS

        with patch.object(gnd, "fetch_rss", side_effect=fake_fetch):
            articles, errors = gnd.collect_news(["TW", "US"], hours=0)
        self.assertEqual(len(articles), 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("地區 TW 抓取失敗", errors[0])

    def test_main_json_envelope_and_delivery(self):
        with (
            patch.object(gnd, "fetch_rss", return_value=SAMPLE_RSS),
            patch("builtins.print") as mock_print,
        ):
            rc = gnd.main(["--regions", "TW", "--hours", "0", "--no-resolve", "--format", "json"])
        self.assertEqual(rc, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertIn("generated_at", payload)
        self.assertTrue(payload["notebook_title"].endswith("_新聞日報"))
        self.assertEqual(len(payload["articles"]), 2)
        self.assertEqual(payload["errors"], [])

    def test_main_returns_nonzero_when_all_resolutions_fail(self):
        with (
            patch.object(gnd, "fetch_rss", return_value=SAMPLE_RSS),
            patch.object(gnd, "resolve_google_news_url", return_value=(None, False, "decode error")),
            patch("builtins.print") as mock_print,
        ):
            rc = gnd.main(["--regions", "TW", "--hours", "0", "--format", "json"])
        self.assertEqual(rc, 1)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(len(payload["errors"]), 2)
        self.assertEqual(payload["articles"], [])

    def test_enrich_backfill_and_prefer_text(self):
        candidates = [
            gnd.NewsArticle("US", "Story 1", "Reuters", "https://news.google.com/rss/articles/1", None),
            gnd.NewsArticle("US", "Story 2", "CNBC", "https://news.google.com/rss/articles/2", None),
            gnd.NewsArticle("US", "Story 3", "AP", "https://news.google.com/rss/articles/3", None),
        ]
        resolved = [
            ("https://www.reuters.com/1", True, None),
            ("https://www.cnbc.com/2", True, None),
            ("https://apnews.com/3", True, None),
        ]
        excerpts = [
            ("", "正文抽取 HTTP 401"),
            ("CNBC full article body text here.", None),
            ("AP full article body text here.", None),
        ]
        with (
            patch.object(gnd, "resolve_google_news_url", side_effect=resolved),
            patch.object(gnd, "_fetch_excerpt", side_effect=excerpts),
        ):
            kept, errors = gnd.enrich_articles(candidates, limit_per_region=2, delay=0, prefer_text=True)

        self.assertEqual(len(kept), 2)
        self.assertEqual([a.title for a in kept], ["Story 2", "Story 3"])
        self.assertTrue(all(a.delivery == "text" for a in kept))
        self.assertEqual(len(errors), 1)
        self.assertIn("HTTP 401", errors[0])
        self.assertEqual(candidates[0].delivery, "skip")

    def test_enrich_default_mode_backfill_and_limit_cap(self):
        candidates = [
            gnd.NewsArticle("US", "Story 1", "Reuters", "https://news.google.com/rss/articles/1", None),
            gnd.NewsArticle("US", "Story 2", "AP", "https://news.google.com/rss/articles/2", None),
            gnd.NewsArticle("US", "Story 3", "BBC", "https://news.google.com/rss/articles/3", None),
        ]
        resolved = [
            ("https://www.reuters.com/1", True, None),
            ("https://apnews.com/2", True, None),
            ("https://www.bbc.com/3", True, None),
        ]
        with (
            patch.object(gnd, "resolve_google_news_url", side_effect=resolved),
            patch.object(gnd, "_fetch_excerpt", return_value=("", "正文抽取 HTTP 401")),
        ):
            kept, errors = gnd.enrich_articles(candidates, limit_per_region=1, delay=0, prefer_text=False)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].title, "Story 2")
        self.assertEqual(kept[0].delivery, "url")
        self.assertEqual(len(errors), 1)
        self.assertIn("HTTP 401", errors[0])


if __name__ == "__main__":
    unittest.main()
