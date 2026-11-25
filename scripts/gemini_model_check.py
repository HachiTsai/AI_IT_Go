"""Gemini 模型每月重測（Jira HAC-11）。

對固定的一批文字與影像模型各做一次最小 generateContent（只確認有回應，不生成圖片），與上次可見模型清單比較，
寫出 knowledge/raw 來源檔，並可在 Jira HAC-11 留言。只用標準函式庫。

環境變數：
- GEMINI_API_KEY（或 Gemini_API）：Gemini 金鑰，必填
- ATLASSIAN_EMAIL、ATLASSIAN_API_TOKEN：Jira 留言用，缺少時略過 Jira

用法：
    python scripts/gemini_model_check.py --dry-run   # 只驗證金鑰、models.list 與 Jira 憑證，不呼叫 generateContent
    python scripts/gemini_model_check.py             # 寫檔並在 HAC-11 留言
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "gemini-visible-models.json"
RAW_DIR = ROOT / "knowledge" / "raw"
API = "https://generativelanguage.googleapis.com/v1beta"
JIRA_SITE = "https://hachitsai.atlassian.net"
JIRA_ISSUE = "HAC-11"
TZ = dt.timezone(dt.timedelta(hours=8))

TEXT_MODELS = [
    "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash",
    "gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
    "gemini-4-argon", "gemini-4-carbon", "gemini-4-hydrogen", "gemini-pro-latest",
    "gemini-flash-latest",
]
IMAGE_MODELS = [
    "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview",
    "gemini-3-pro-image", "nano-banana-pro-preview", "gemini-2.5-flash-image",
    "gemini-nano-banana-2.1",
]
# 只確認模型有回應，不要求生成圖片，並限制輸出長度以壓低費用
PROMPT = "Reply with exactly one word: OK"
MAX_OUTPUT_TOKENS = 8


def _request(url: str, *, data: dict | None = None, headers: dict | None = None, timeout: int = 120):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read() or b"{}")
        except json.JSONDecodeError:
            payload = {}
        return e.code, payload


def list_models(key: str) -> tuple[list[str], list[str]]:
    """回傳（所有可見模型, 支援 generateContent 的模型），名稱不含 models/ 前綴。"""
    visible, generate = [], []
    token = ""
    while True:
        url = f"{API}/models?pageSize=1000"
        if token:
            url += f"&pageToken={token}"
        status, payload = _request(url, headers={"x-goog-api-key": key})
        if status != 200:
            raise RuntimeError(f"models.list 失敗：HTTP {status}")
        for m in payload.get("models", []):
            name = m["name"].removeprefix("models/")
            visible.append(name)
            if "generateContent" in m.get("supportedGenerationMethods", []):
                generate.append(name)
        token = payload.get("nextPageToken", "")
        if not token:
            return sorted(visible), sorted(generate)


def check_model(key: str, model: str, kind: str) -> dict:
    data = {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
    }
    if kind == "image":
        # 影像模型也只要求文字回覆，不生成圖片
        data["generationConfig"]["responseModalities"] = ["TEXT"]
    result: dict = {}
    for attempt in range(3):
        status, payload = _request(f"{API}/models/{model}:generateContent", data=data,
                                   headers={"x-goog-api-key": key})
        result = evaluate(model, kind, status, payload)
        # 成功、或非暫時性錯誤（4xx 且非 429）就停
        if result["ok"] or (status != 200 and status < 500 and status != 429):
            break
        time.sleep(5 * (attempt + 1))
    return result


def evaluate(model: str, kind: str, status: int, payload: dict) -> dict:
    """HTTP 200 且有候選回應即視為可用（純函式，供測試）。"""
    result = {"model": model, "kind": kind, "status": status, "ok": False, "note": ""}
    if status != 200:
        result["note"] = payload.get("error", {}).get("message", "")[:120]
        return result
    candidates = payload.get("candidates", [])
    parts = [p for c in candidates for p in c.get("content", {}).get("parts", [])]
    text = "".join(p.get("text", "") for p in parts).strip()
    result["ok"] = bool(candidates)
    if text:
        result["note"] = f"有回應：{text[:20]}"
    elif candidates:
        result["note"] = f"有回應（{candidates[0].get('finishReason', '無文字')}）"
    else:
        result["note"] = "沒有回應"
    return result


def compare(previous: dict, visible: list[str], generate: list[str]) -> dict:
    prev_visible = set(previous.get("visible", []))
    return {
        "prev_date": previous.get("date", ""),
        "prev_visible_count": len(prev_visible),
        "prev_generate_count": len(previous.get("generate", [])),
        "added": sorted(set(visible) - prev_visible) if prev_visible else [],
        "removed": sorted(prev_visible - set(visible)) if prev_visible else [],
    }


def render_markdown(date: str, results: list[dict], visible: list[str], generate: list[str], diff: dict) -> str:
    ok = sum(r["ok"] for r in results)
    lines = [
        f"# Gemini 金鑰可用模型檢查（{date}）",
        "",
        "- 執行者：GitHub Actions（scripts/gemini_model_check.py，金鑰未寫入本檔）",
        f"- 測試方式：`models.list` 取得清單後，對同一批 {len(results)} 個文字與影像模型各做一次最小 `generateContent` 呼叫，只確認有回應（影像模型不生成圖片，輸出上限 {MAX_OUTPUT_TOKENS} tokens）",
        "",
        "## 結果",
        "",
        f"合計測試 {len(results)} 個，可用 {ok} 個，失敗 {len(results) - ok} 個。",
        "",
        "| 模型 | 類型 | 結果 | HTTP | 說明 |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in results:
        kind = "文字" if r["kind"] == "text" else "影像"
        note = r["note"].replace("|", "/").replace("\n", " ")
        lines.append(f"| `{r['model']}` | {kind} | {'可用' if r['ok'] else '失敗'} | {r['status']} | {note} |")
    lines += ["", f"## 與 {diff['prev_date'] or '上次'} 紀錄比較", ""]
    if diff["prev_visible_count"]:
        lines.append(f"- 金鑰可見模型由 {diff['prev_visible_count']} 個變為 {len(visible)} 個，"
                     f"支援 `generateContent` 的由 {diff['prev_generate_count']} 個變為 {len(generate)} 個。")
        lines.append("- 新增可見：" + ("、".join(f"`{m}`" for m in diff["added"]) or "無") + "。")
        lines.append("- 不再出現：" + ("、".join(f"`{m}`" for m in diff["removed"]) or "無") + "。")
    else:
        lines.append(f"- 沒有上次的可見模型清單，本次可見 {len(visible)} 個，支援 `generateContent` 的 {len(generate)} 個。")
    lines += ["", "## 附錄：支援 generateContent 的模型", ""]
    lines += [f"- `{m}`" for m in generate]
    return "\n".join(lines) + "\n"


def jira_comment(date: str, results: list[dict], visible: list[str], generate: list[str], diff: dict) -> str:
    """Jira wiki markup 留言（REST API v2）。"""
    ok = sum(r["ok"] for r in results)
    failed = [r["model"] for r in results if not r["ok"]]
    rows = [
        f"h4. {date} 重測結果（執行者：GitHub Actions）",
        "",
        f"* 測試 {len(results)} 個模型，{ok} 個可用，失敗 {len(results) - ok} 個"
        + (f"：{', '.join(failed)}" if failed else "") + "。",
        f"* 金鑰可見 {len(visible)} 個模型，其中 {len(generate)} 個支援 generateContent。",
    ]
    if diff["prev_visible_count"]:
        rows.append("* 新增可見：" + (", ".join(diff["added"]) or "無"))
        rows.append("* 不再出現：" + (", ".join(diff["removed"]) or "無"))
    rows.append("* 完整結果：knowledge/raw 新增的 gemini-model-check 檔（PR 待 Claude 審核並同步 wiki 與 Drive）")
    return "\n".join(rows)


def raw_path(raw_dir: Path, date: str) -> Path:
    """回傳不覆蓋既有來源檔的路徑（同日已有檔案時加上 -2、-3…）。"""
    out = raw_dir / f"gemini-model-check-{date}.md"
    n = 2
    while out.exists():
        out = raw_dir / f"gemini-model-check-{date}-{n}.md"
        n += 1
    return out


def _jira_headers() -> dict | None:
    email, token = os.environ.get("ATLASSIAN_EMAIL"), os.environ.get("ATLASSIAN_API_TOKEN")
    if not (email and token):
        return None
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {"Authorization": f"Basic {auth}", "Accept": "application/json"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="只驗證金鑰、models.list 與 Jira 憑證，不呼叫 generateContent")
    parser.add_argument("--date", default=dt.datetime.now(TZ).date().isoformat())
    args = parser.parse_args(argv)

    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("Gemini_API")
    if not key:
        print("缺少 GEMINI_API_KEY", file=sys.stderr)
        return 2
    jira = _jira_headers()
    print(f"Jira 憑證：{'已設定' if jira else '未設定（略過留言）'}")
    if jira:
        status, me = _request(f"{JIRA_SITE}/rest/api/2/myself", headers=jira)
        print(f"Jira 驗證：HTTP {status}")
        if status != 200:
            jira = None

    visible, generate = list_models(key)
    if args.dry_run:
        # dry run 只驗證金鑰與 models.list，不呼叫 generateContent，避免消耗付費額度
        missing = [m for m in TEXT_MODELS + IMAGE_MODELS if m not in generate]
        print(f"dry run：可見 {len(visible)}，generateContent {len(generate)}；測試清單中不可用：{missing or '無'}")
        return 0
    results = [check_model(key, m, "text") for m in TEXT_MODELS]
    results += [check_model(key, m, "image") for m in IMAGE_MODELS]
    previous = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.is_file() else {}
    diff = compare(previous, visible, generate)

    ok = sum(r["ok"] for r in results)
    print(f"可用 {ok}/{len(results)}；可見 {len(visible)}，generateContent {len(generate)}")
    print(f"新增：{diff['added']}；不再出現：{diff['removed']}")
    for r in results:
        if not r["ok"]:
            print(f"失敗：{r['model']} HTTP {r['status']} {r['note']}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(render_markdown(args.date, results, visible, generate, diff))
    out = raw_path(RAW_DIR, args.date)
    out.write_text(render_markdown(args.date, results, visible, generate, diff), encoding="utf-8")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"date": args.date, "visible": visible, "generate": generate},
                                     ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已寫入 {out.relative_to(ROOT)}")
    if jira:
        status, _ = _request(f"{JIRA_SITE}/rest/api/2/issue/{JIRA_ISSUE}/comment",
                             data={"body": jira_comment(args.date, results, visible, generate, diff)},
                             headers=jira)
        print(f"Jira 留言：HTTP {status}")
        if status not in (200, 201):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
