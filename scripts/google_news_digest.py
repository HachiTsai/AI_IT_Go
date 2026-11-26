"""抓取多國 Google News RSS、解析來源與時間，並進行標題去重與摘要輸出。"""

from __future__ import annotations

import argparse
import getpass
import html
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
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
PERSPECTIVE_PRESETS: dict[str, str] = {
    "analyst": "資深科技與產業情報分析師，重視跨國敘事差異與戰略訊號",
    "investor": "專注科技與台美股供應鏈的機構投資人，聚焦營收動能、資本支出、估值與風險因子",
    "engineer": "資深系統與 AI 架構師，聚焦技術標準、API/協定演進、基礎設施瓶頸與實作影響",
    "security": "資安架構與治理專家，聚焦供應鏈風險、權限控管、合規要求與攻防威脅",
    "pm": "AI 產品經理，聚焦使用者需求、商業模式變化、競品動向與產品落地機會",
}


@dataclass
class NewsArticle:
    """單篇 Google News RSS 解析結果。"""

    region: str
    title: str
    source: str
    link: str
    published_at: datetime | None
    related_sources: list[str] = field(default_factory=list)
    resolved_url: str | None = None
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


def resolve_google_news_url(url: str, client: httpx.Client) -> str:
    """透過 Google News batchexecute 解碼跳轉連結為原始媒體 URL；失敗時回傳原網址。"""
    if "news.google.com" not in url:
        return url
    try:
        resp = client.get(url)
        resp.raise_for_status()
        m = re.search(r'data-p="([^"]+)"', resp.text)
        if not m:
            return str(resp.url)
        dp = html.unescape(m.group(1))
        obj = json.loads("[" + dp[4:] if dp.startswith("%.@.") else dp)
        article_id, ts, sig = obj[1], obj[6], obj[7]
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
        batch = client.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute",
            data={"f.req": json.dumps(payload)},
            headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        )
        batch.raise_for_status()
        match_res = re.search(r'\["garturlres","([^"]+)"', batch.text.replace('\\"', '"'))
        if match_res:
            return match_res.group(1)
    except Exception:
        pass
    return url


def enrich_articles(articles: list[NewsArticle], max_chars: int = 2000, timeout: float = 10.0) -> None:
    """為新聞清單補齊原始媒體 URL 與正文摘錄（失敗時靜默降級保留標題）。"""
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        for article in articles:
            real_url = resolve_google_news_url(article.link, client)
            article.resolved_url = real_url
            try:
                resp = client.get(real_url)
                if resp.status_code == 200 and "html" in resp.headers.get("content-type", "").lower():
                    article.excerpt = extract_paragraphs(resp.text, max_chars=max_chars)
            except Exception:
                continue


def get_gemini_api_key() -> str:
    """優先從環境變數讀取 GEMINI_API_KEY，若無則向 macOS Keychain 取用。"""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Google_Generative_API_KEY")
    if api_key:
        return api_key.strip()
    return subprocess.check_output(
        ["security", "find-generic-password", "-a", getpass.getuser(), "-s", "GEMINI_API_KEY", "-w"],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def resolve_perspective(perspective: str | None) -> str:
    """將視角別名或自訂文字轉為分析師角色描述。"""
    if not perspective or not perspective.strip():
        return PERSPECTIVE_PRESETS["analyst"]
    key = perspective.strip().lower()
    return PERSPECTIVE_PRESETS.get(key, perspective.strip())


def analyze_with_gemini(
    articles: list[NewsArticle],
    query: str | None,
    model: str = "gemini-2.5-pro",
    perspective: str | None = None,
    api_key: str | None = None,
    timeout: float = 120.0,
) -> tuple[str, dict[str, int]]:
    """呼叫 Gemini API 產出指定視角的跨國新聞溫差分析與 Mermaid 視覺化簡報。"""
    key = api_key or get_gemini_api_key()
    topic = query or "今日頭條"
    role_desc = resolve_perspective(perspective)
    items_payload = []
    for i, a in enumerate(articles, 1):
        ts = a.published_at.astimezone().strftime("%Y-%m-%d %H:%M") if a.published_at else "未知時間"
        url = a.resolved_url or a.link
        items_payload.append(
            f"[{i}] 地區: {a.region} | 媒體: {a.source} | 時間: {ts}\n"
            f"標題: {a.title}\n"
            f"連結: {url}\n"
            f"正文節錄: {a.excerpt or '（未能取得正文，請依標題與來源脈絡分析）'}"
        )

    prompt = (
        f"請以「{role_desc}」的角度與立場進行分析。\n"
        f"請根據以下針對「{topic}」抓取的多國新聞資料，"
        "使用繁體中文撰寫一份高密度的情報簡報（所有觀察、溫差解讀與建議都必須緊扣上述指定視角）：\n\n"
        "請包含以下四個部分：\n"
        "1. **核心事件主線**：濃縮今日最重要的進展，附註媒體來源與連結。\n"
        "2. **跨國新聞溫差分析**：比較各地區（如 TW 與 US）媒體關注焦點、敘事角度與背後訊號的差異。\n"
        "3. **Mermaid 結構圖**：請繪製一張 `flowchart LR` 或 `flowchart TD` 圖表，"
        "視覺化呈現「核心驅動事件 → 各地區焦點差異 → 產業／技術影響」。"
        "（節點標籤請務必用雙引號包住，例如 `A[\"標籤文字\"]`，且不要使用 HTML 標籤）。\n"
        "4. **重點 Takeaways 與後續追蹤建議**：2～3 點具體洞察。\n\n"
        "--- 新聞資料 ---\n\n" + "\n\n".join(items_payload)
    )

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(endpoint, params={"key": key}, json=body)
        resp.raise_for_status()
        data = resp.json()

    candidates = data.get("candidates", [])
    text = ""
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
    usage = data.get("usageMetadata", {})
    return text.strip(), usage


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
    parser.add_argument("--analyze", action="store_true", help="還原連結、抽取正文並呼叫 Gemini 產出跨國溫差簡報")
    parser.add_argument("--model", default="gemini-2.5-pro", help="搭配 --analyze 使用的 Gemini 模型（預設 gemini-2.5-pro）")
    parser.add_argument(
        "-p",
        "--perspective",
        default=None,
        help="指定分析角度：支援預設別名 (analyst, investor, engineer, security, pm) 或直接輸入自訂描述",
    )
    parser.add_argument("--max-chars", type=int, default=2000, help="每篇新聞最多抽取幾字元正文（預設 2000）")
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

    if args.analyze:
        enrich_articles(articles, max_chars=args.max_chars)
        report, usage = analyze_with_gemini(
            articles,
            query=args.query,
            model=args.model,
            perspective=args.perspective,
        )
        prompt_tk = usage.get("promptTokenCount", 0)
        cand_tk = usage.get("candidatesTokenCount", 0)
        thought_tk = usage.get("thoughtsTokenCount", 0)
        meta_line = (
            f"\n\n---\n_模型：`{args.model}` | "
            f"Tokens：input={prompt_tk:,}, output={cand_tk:,}, thoughts={thought_tk:,}_\n"
        )
        output_text = report + meta_line
    elif args.format == "json":
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
