# Google 新聞 × NotebookLM 零 API 費用自動化架構（2026-11-26）

## 1. 角色分工（Issue #40 評估定案）

- `scripts/google_news_digest.py`：負責免費抓取 Google News RSS、地區內標題去重、連結還原、判斷傳送方式（`url` 或 `text`），並輸出外殼 JSON `{generated_at, notebook_title, articles, errors}`。
- 腳本不再依賴 `GEMINI_API_KEY` 或 macOS Keychain，僅保留純抓取、還原與正文備援能力。
- Antigravity Automation：依 `notebook_title`（`YYYY-MM-DD_新聞日報`）建立當天筆記本、依 `delivery` 送入來源、檢查 `FAILED` 來源並改用正文重送、回報執行結果。
- NotebookLM（`gemini-notebook` MCP）：免費承接摘要、跨國溫差比對、指定視角追問與簡報／心智圖轉換。

## 2. 實測限制與防護機制

- 被擋網域清單（`BLOCKED_DOMAINS`）：`tw.stock.yahoo.com`、`cnbc.com`、`reuters.com` 實測會封鎖 NotebookLM 伺服器端抓取，命中時標記 `delivery="text"` 並僅對這些網域抽取正文 `excerpt`。
- 連結還原失敗處理：`resolve_google_news_url` 失敗時標記 `resolve_ok=false` 並記錄進 `errors`，不默默回傳 `news.google.com` 跳轉網址；若整批還原皆失敗則回傳非零結束碼。
- 官方 MCP 不提供 `delete_source` 與 `delete_notebook`，舊筆記本由人工於 NotebookLM 網頁版定期清理。
