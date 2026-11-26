"""抓取多國 Google News RSS、去重、還原原始網址並輸出給 NotebookLM / 自動化流程。"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import httpx

REGION_PRESETS: dict[str, tuple[str, str, str]] = {
    "TW": ("zh-TW", "TW", "TW:zh-Hant"),
    "US": ("en-US", "US", "US:en"),
    "JP": ("ja", "JP", "JP:ja"),
    "GB": ("en-GB", "GB", "GB:en"),
    "HK": ("zh-HK", "HK", "HK:zh-Hant"),
}

# 實測會封鎖 NotebookLM 直接抓網頁的網域，命中時改由本機抽取正文以 textContent 送出
BLOCKED_DOMAINS: tuple[str, ...] = (
    "tw.stock.yahoo.com",
    "finance.yahoo.com",
    "cnbc.com",
    "reuters.com",
)

DEFAULT_TIMEOUT = 15.0
DEFAULT_SIMILARITY_THRESHOLD = 0.72
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class NewsArticle:
    """單篇 Google News RSS 解析與還原結果。"""

    region: str
    title: str
    source: str
    link: str
    published_at: datetime | None
    related_sources: list[str] = field(default_factory=list)
    resolved_url: str | None = None
    resolve_ok: bool = False
    delivery: str = "url"
    excerpt: str = ""

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
    """依地區內標題相似度去重，保留第一筆出現的新聞並彙整相關來源。"""
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


class _ParagraphExtractor(HTMLParser):
    """從 HTML 提取主要段落文字，略過導覽列、頁尾與腳本。"""

    _SKIP_TAGS = frozenset({"script", "style", "noscript", "nav", "header", "footer", "aside", "svg"})

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._in_p = False
        self._current: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "p" and self._skip_depth == 0:
            self._in_p = True
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag == "p" and self._in_p:
            text = " ".join("".join(self._current).split())
            if len(text) >= 20:
                self.paragraphs.append(text)
            self._in_p = False
            self._current = []

    def handle_data(self, data: str) -> None:
        if self._in_p and self._skip_depth == 0:
            self._current.append(data)


def extract_paragraphs(html_text: str, max_chars: int = 2000) -> str:
    """從 HTML 中抽取前 max_chars 字元的新聞段落。"""
    parser = _ParagraphExtractor()
    parser.feed(html_text)
    combined = "\n".join(parser.paragraphs)
    if len(combined) > max_chars:
        return combined[:max_chars].rstrip() + "…"
    return combined


def is_blocked_domain(url: str, blocked: tuple[str, ...] = BLOCKED_DOMAINS) -> bool:
    """判斷網址是否屬於已知會封鎖 NotebookLM 爬蟲的網域。"""
    host = (urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith(f".{domain}") for domain in blocked)


def _request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    retries: int = 2,
    **kwargs: object,
) -> httpx.Response:
    for attempt in range(retries + 1):
        resp = client.request(method, url, **kwargs)
        if resp.status_code in (429, 502, 503, 504) and attempt < retries:
            time.sleep(1.5 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError(f"請求失敗: {url}")


def decode_data_p_params(page_html: str) -> tuple[str, int, str]:
    """從 Google News 跳轉頁 HTML 的 data-p 屬性解析 (article_id, timestamp, signature)。"""
    m = re.search(r'data-p="([^"]+)"', page_html)
    if not m:
        raise ValueError("頁面缺少 data-p 屬性")
    dp = html.unescape(m.group(1))
    obj = json.loads("[" + dp[4:] if dp.startswith("%.@.") else dp)
    return str(obj[1]), int(obj[6]), str(obj[7])


def resolve_google_news_url(
    url: str,
    client: httpx.Client,
    retries: int = 2,
) -> tuple[str | None, bool, str | None]:
    """透過 Google News batchexecute 解碼跳轉連結為原始媒體 URL。

    回傳 `(resolved_url, resolve_ok, error_message)`；失敗時不回傳原跳轉網址。
    """
    if "news.google.com" not in url:
        return url, True, None

    try:
        resp = _request_with_retry(client, "GET", url, retries=retries)
        article_id, ts, sig = decode_data_p_params(resp.text)
        inner = json.dumps(
            [
                "garturlreq",
                [
                    ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
                    "X",
                    "X",
                    1,
                    [1, 1, 1],
                    1,
                    1,
                    None,
                    0,
                    0,
                    None,
                    0,
                ],
                article_id,
                ts,
                sig,
            ]
        )
        payload = [[["Fbv4je", inner, None, "generic"]]]
        batch = _request_with_retry(
            client,
            "POST",
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            retries=retries,
            data={"f.req": json.dumps(payload)},
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        )
        match_res = re.search(r'\["garturlres","([^"]+)"', batch.text.replace('\\"', '"'))
        if not match_res:
            return None, False, "batchexecute 回應未包含 garturlres"
        return match_res.group(1), True, None
    except Exception as exc:
        return None, False, f"連結還原失敗 ({exc})"


def _fetch_excerpt(url: str, client: httpx.Client, max_chars: int) -> tuple[str, str | None]:
    """抓取網頁並抽取正文段落，回傳 (excerpt, error_message)。"""
    try:
        resp = client.get(url)
        if resp.status_code != 200:
            return "", f"正文抽取 HTTP {resp.status_code}"
        if "html" not in resp.headers.get("content-type", "").lower():
            return "", "非 HTML 內容，略過正文抽取"
        text = extract_paragraphs(resp.text, max_chars=max_chars)
        if not text:
            return "", "正文抽取結果為空"
        return text, None
    except Exception as exc:
        return "", f"正文抽取失敗 ({exc})"


def enrich_articles(
    articles: list[NewsArticle],
    limit_per_region: int | None = None,
    max_chars: int = 2000,
    timeout: float = 10.0,
    delay: float = 0.25,
    prefer_text: bool = False,
) -> tuple[list[NewsArticle], list[str]]:
    """還原原始網址、判斷傳送方式並支援失敗遞補；回傳 `(deliverable_articles, errors)`。"""
    kept: list[NewsArticle] = []
    kept_counts: dict[str, int] = {}
    errors: list[str] = []
    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for idx, article in enumerate(articles):
            if limit_per_region and kept_counts.get(article.region, 0) >= limit_per_region:
                continue
            if idx > 0 and delay > 0:
                time.sleep(delay)

            real_url, ok, err = resolve_google_news_url(article.link, client)
            article.resolve_ok = ok
            article.resolved_url = real_url
            if not ok or not real_url:
                article.delivery = "skip"
                if err:
                    errors.append(f"[{article.region}] {article.title}: {err}")
                continue

            if prefer_text or is_blocked_domain(real_url):
                excerpt, ex_err = _fetch_excerpt(real_url, client, max_chars=max_chars)
                if excerpt:
                    article.delivery = "text"
                    article.excerpt = excerpt
                    kept.append(article)
                    kept_counts[article.region] = kept_counts.get(article.region, 0) + 1
                else:
                    article.delivery = "skip"
                    errors.append(f"[{article.region}] {article.title}: {ex_err}")
            else:
                article.delivery = "url"
                kept.append(article)
                kept_counts[article.region] = kept_counts.get(article.region, 0) + 1

    return kept, errors


def render_markdown(articles: list[NewsArticle], query: str | None = None, errors: list[str] | None = None) -> str:
    """將去重後的新聞清單格式化為 Markdown 摘要。"""
    header = f"# Google 新聞摘要：{query}" if query else "# Google 新聞摘要（頭條）"
    lines = [header, ""]
    if not articles:
        lines.append("目前沒有符合條件的新聞。")
    else:
        by_region: dict[str, list[NewsArticle]] = {}
        for article in articles:
            by_region.setdefault(article.region, []).append(article)

        for region, items in by_region.items():
            lines.append(f"## 地區：{region}（共 {len(items)} 則）")
            lines.append("")
            for i, item in enumerate(items, 1):
                ts = item.published_at.astimezone().strftime("%Y-%m-%d %H:%M") if item.published_at else "未知時間"
                target_url = item.resolved_url or item.link
                extra = f"（另有 {', '.join(item.related_sources)} 報導）" if item.related_sources else ""
                lines.append(f"{i}. **[{item.title}]({target_url})** — {item.source} · {ts}{extra}")
            lines.append("")

    if errors:
        lines.append("## 錯誤紀錄")
        lines.append("")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def collect_news(
    regions: list[str],
    query: str | None = None,
    limit: int = 10,
    hours: int | None = 48,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[list[NewsArticle], list[str]]:
    """抓取指定地區的新聞、篩選時間、去重；單一地區失敗時記錄錯誤並繼續。"""
    all_articles: list[NewsArticle] = []
    errors: list[str] = []
    for idx, region in enumerate(regions):
        if idx > 0:
            time.sleep(0.3)
        try:
            url = build_rss_url(region, query=query)
            xml_text = fetch_rss(url)
            parsed = parse_rss_xml(xml_text, region=region)
            filtered = filter_by_hours(parsed, hours=hours)
            deduped = dedupe_articles(filtered, threshold=threshold)
            deduped.sort(key=lambda a: a.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
            all_articles.extend(deduped[:limit])
        except Exception as exc:
            errors.append(f"地區 {region} 抓取失敗: {exc}")
    return all_articles, errors


def build_notebook_title(now: datetime | None = None) -> str:
    """產生當天筆記本名稱（YYYY-MM-DD_新聞日報）。"""
    ref = now or datetime.now().astimezone()
    return f"{ref.strftime('%Y-%m-%d')}_新聞日報"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="抓取多國 Google News RSS、去重並還原原始網址")
    parser.add_argument("-q", "--query", default=None, help="搜尋關鍵字（省略時抓各區頭條）")
    parser.add_argument(
        "-r",
        "--regions",
        default="TW,US",
        help="逗號分隔的地區代碼，預設 TW,US（支援: TW, US, JP, GB, HK）",
    )
    parser.add_argument("-n", "--limit", type=int, default=10, help="每個地區最多保留幾則（預設 10）")
    parser.add_argument("--hours", type=int, default=48, help="只保留最近幾小時內的新聞，0 表示不限（預設 48）")
    parser.add_argument("--no-resolve", action="store_true", help="略過原始網址還原與被擋網域正文抽取（僅供除錯）")
    parser.add_argument(
        "--prefer-text",
        action="store_true",
        help="優先本機抽取所有文章正文改用 textContent 送出，抽不到正文者直接跳過並自動遞補",
    )
    parser.add_argument("--max-chars", type=int, default=2000, help="抽取正文上限字元數（預設 2000）")
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

    pool_limit = args.limit if args.no_resolve else args.limit * 3
    articles, errors = collect_news(
        regions=regions,
        query=args.query,
        limit=pool_limit,
        hours=args.hours,
    )

    if not args.no_resolve and articles:
        articles, enrich_errors = enrich_articles(
            articles,
            limit_per_region=args.limit,
            max_chars=args.max_chars,
            prefer_text=args.prefer_text,
        )
        errors.extend(enrich_errors)

    now = datetime.now().astimezone()
    if args.format == "json":
        envelope = {
            "generated_at": now.isoformat(),
            "notebook_title": build_notebook_title(now),
            "articles": [a.to_dict() for a in articles],
            "errors": errors,
        }
        output_text = json.dumps(envelope, ensure_ascii=False, indent=2) + "\n"
    else:
        output_text = render_markdown(articles, query=args.query, errors=errors)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    else:
        print(output_text, end="")

    if not articles and errors:
        return 1
    if not args.no_resolve and articles and not any(a.resolve_ok for a in articles):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
