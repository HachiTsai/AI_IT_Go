"""抓取多國 Google News RSS、解析來源與時間，並進行標題去重與摘要輸出。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus

import httpx

REGION_PRESETS: dict[str, tuple[str, str, str]] = {
    "TW": ("zh-TW", "TW", "TW:zh-Hant"),
    "US": ("en-US", "US", "US:en"),
    "JP": ("ja", "JP", "JP:ja"),
    "GB": ("en-GB", "GB", "GB:en"),
    "HK": ("zh-HK", "HK", "HK:zh-Hant"),
}

DEFAULT_TIMEOUT = 15.0
DEFAULT_SIMILARITY_THRESHOLD = 0.72
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class NewsArticle:
    """單篇 Google News RSS 解析結果。"""

    region: str
    title: str
    source: str
    link: str
    published_at: datetime | None
    related_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["published_at"] = self.published_at.isoformat() if self.published_at else None
        return data


def build_rss_url(region: str, query: str | None = None) -> str:
    """依地區代碼與關鍵字組合 Google News RSS URL。"""
    key = region.strip().upper()
    if key not in REGION_PRESETS:
        supported = ", ".join(sorted(REGION_PRESETS))
        raise ValueError(f"不支援的地區代碼: {region!r}（支援: {supported}）")

    hl, gl, ceid = REGION_PRESETS[key]
    params = f"hl={hl}&gl={gl}&ceid={quote_plus(ceid)}"
    if query and query.strip():
        return f"https://news.google.com/rss/search?q={quote_plus(query.strip())}&{params}"
    return f"https://news.google.com/rss?{params}"


def _clean_title_and_source(raw_title: str, raw_source: str) -> tuple[str, str]:
    """移除 Google News 標題尾端的 ` - 媒體名稱` 後綴，並補齊來源名稱。"""
    title = raw_title.strip()
    source = raw_source.strip()
    if " - " in title:
        head, tail = title.rsplit(" - ", 1)
        if not source or tail.strip() == source:
            title = head.strip()
            source = source or tail.strip()
    return title, source or "Unknown"


def _parse_pub_date(raw_date: str | None) -> datetime | None:
    if not raw_date or not raw_date.strip():
        return None
    try:
        dt = parsedate_to_datetime(raw_date.strip())
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_rss_xml(xml_text: str, region: str) -> list[NewsArticle]:
    """解析 Google News RSS XML 內容為 NewsArticle 清單。"""
    root = ET.fromstring(xml_text)
    articles: list[NewsArticle] = []
    for item in root.findall("./channel/item"):
        raw_title = item.findtext("title") or ""
        raw_source = item.findtext("source") or ""
        link = (item.findtext("link") or "").strip()
        pub_date = _parse_pub_date(item.findtext("pubDate"))
        title, source = _clean_title_and_source(raw_title, raw_source)
        if not title or not link:
            continue
        articles.append(
            NewsArticle(
                region=region.upper(),
                title=title,
                source=source,
                link=link,
                published_at=pub_date,
            )
        )
    return articles


def _normalize_title(title: str) -> str:
    """正規化標題用於去重比對（轉小寫並移除標點與空白）。"""
    return re.sub(r"[\W_]+", "", title.lower())


def dedupe_articles(
    articles: list[NewsArticle],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[NewsArticle]:
    """依地區內標題相似度去重，保留較早或第一筆出現的新聞並彙整相關來源。"""
    kept: list[NewsArticle] = []
    kept_norms: list[str] = []

    for article in articles:
        norm = _normalize_title(article.title)
        matched_idx: int | None = None
        for idx, existing in enumerate(kept):
            if existing.region != article.region:
                continue
            if norm == kept_norms[idx] or SequenceMatcher(None, norm, kept_norms[idx]).ratio() >= threshold:
                matched_idx = idx
                break

        if matched_idx is None:
            kept.append(article)
            kept_norms.append(norm)
        else:
            target = kept[matched_idx]
            if article.source != target.source and article.source not in target.related_sources:
                target.related_sources.append(article.source)

    return kept


def filter_by_hours(
    articles: list[NewsArticle],
    hours: int | None,
    now: datetime | None = None,
) -> list[NewsArticle]:
    """只保留最近 N 小時內的新聞（hours 為 None 或 <= 0 時不篩選）。"""
    if not hours or hours <= 0:
        return articles
    ref = now or datetime.now(UTC)
    cutoff = ref - timedelta(hours=hours)
    return [a for a in articles if a.published_at is None or a.published_at >= cutoff]


def fetch_rss(url: str, timeout: float = DEFAULT_TIMEOUT, retries: int = 2) -> str:
    """透過 HTTP GET 下載 RSS XML 文字，遇到 429 或暫時性錯誤時退避重試。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    }
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for attempt in range(retries + 1):
            resp = client.get(url)
            if resp.status_code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.text
    raise RuntimeError(f"無法取得 RSS: {url}")


def render_markdown(articles: list[NewsArticle], query: str | None = None) -> str:
    """將去重後的新聞清單格式化為 Markdown 摘要。"""
    header = f"# Google 新聞摘要：{query}" if query else "# Google 新聞摘要（頭條）"
    lines = [header, ""]
    if not articles:
        lines.append("目前沒有符合條件的新聞。")
        return "\n".join(lines)

    by_region: dict[str, list[NewsArticle]] = {}
    for article in articles:
        by_region.setdefault(article.region, []).append(article)

    for region, items in by_region.items():
        lines.append(f"## 地區：{region}（共 {len(items)} 則）")
        lines.append("")
        for i, item in enumerate(items, 1):
            ts = item.published_at.astimezone().strftime("%Y-%m-%d %H:%M") if item.published_at else "未知時間"
            extra = f"（另有 {', '.join(item.related_sources)} 報導）" if item.related_sources else ""
            lines.append(f"{i}. **[{item.title}]({item.link})** — {item.source} · {ts}{extra}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def collect_news(
    regions: list[str],
    query: str | None = None,
    limit: int = 10,
    hours: int | None = 48,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[NewsArticle]:
    """抓取指定地區的新聞、篩選時間、去重並依地區截斷數量。"""
    all_articles: list[NewsArticle] = []
    for idx, region in enumerate(regions):
        if idx > 0:
            time.sleep(0.3)
        url = build_rss_url(region, query=query)
        xml_text = fetch_rss(url)
        parsed = parse_rss_xml(xml_text, region=region)
        filtered = filter_by_hours(parsed, hours=hours)
        deduped = dedupe_articles(filtered, threshold=threshold)
        deduped.sort(key=lambda a: a.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        all_articles.extend(deduped[:limit])
    return all_articles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="抓取多國 Google News RSS 並產出去重摘要")
    parser.add_argument("-q", "--query", default=None, help="搜尋關鍵字（省略時抓各區頭條）")
    parser.add_argument(
        "-r",
        "--regions",
        default="TW,US",
        help="逗號分隔的地區代碼，預設 TW,US（支援: TW, US, JP, GB, HK）",
    )
    parser.add_argument("-n", "--limit", type=int, default=10, help="每個地區最多保留幾則（預設 10）")
    parser.add_argument("--hours", type=int, default=48, help="只保留最近幾小時內的新聞，0 表示不限（預設 48）")
    parser.add_argument(
        "-f",
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="輸出格式（預設 markdown）",
    )
    parser.add_argument("-o", "--output", type=Path, default=None, help="選填：將結果寫入指定檔案")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    regions = [r.strip().upper() for r in args.regions.split(",") if r.strip()]
    if not regions:
        parser.error("至少需要指定一個地區代碼")

    articles = collect_news(
        regions=regions,
        query=args.query,
        limit=args.limit,
        hours=args.hours,
    )

    if args.format == "json":
        output_text = json.dumps([a.to_dict() for a in articles], ensure_ascii=False, indent=2) + "\n"
    else:
        output_text = render_markdown(articles, query=args.query)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
