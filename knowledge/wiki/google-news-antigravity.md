---
title: Google 新聞 × Antigravity 結合指南
sources:
  - knowledge/raw/google-news-notebook-architecture-2026-11-26.md
  - knowledge/raw/google-news-backfill-2026-11-26.md
updated: 2026-11-27
---

# Google 新聞 × Antigravity 結合指南

## 核心定位：零 API 費用的「RSS → NotebookLM」自動化情報流

> "腳本不再依賴 `GEMINI_API_KEY` 或 macOS Keychain，僅保留純抓取、還原與正文備援能力。" — knowledge/raw/google-news-notebook-architecture-2026-11-26.md

整個流程分成三層分工：

1. **`scripts/google_news_digest.py`（NT\$ 0）**：抓取多國 Google News RSS、地區內去重、還原原始媒體網址，並輸出 `{generated_at, notebook_title, articles, errors}` JSON。
2. **Antigravity Automation**：透過 `gemini-notebook` MCP 建當天筆記本（`YYYY-MM-DD_新聞日報`）、依 `delivery` 欄位送入來源、檢查失敗來源並以正文重送。
3. **NotebookLM**：免費接手摘要、跨國溫差比對、指定視角追問（投資人／工程師／資安／PM）與簡報轉換。

## 抓取與失敗保護設計

> "被擋網域清單（`BLOCKED_DOMAINS`）：`tw.stock.yahoo.com`、`cnbc.com`、`reuters.com` 實測會封鎖 NotebookLM 伺服器端抓取，命中時標記 `delivery="text"` 並僅對這些網域抽取正文 `excerpt`。" — knowledge/raw/google-news-notebook-architecture-2026-11-26.md

> "連結還原失敗處理：`resolve_google_news_url` 失敗時標記 `resolve_ok=false` 並記錄進 `errors`，不默默回傳 `news.google.com` 跳轉網址；若整批還原皆失敗則回傳非零結束碼。" — knowledge/raw/google-news-notebook-architecture-2026-11-26.md

> "`--prefer-text` 模式：本機先抽取所有文章正文改用 `textContent` 送進 NotebookLM，避開 NotebookLM 雲端爬蟲網域封鎖；本機仍遇 401/403 抽不到正文者則淘汰並遞補。" — knowledge/raw/google-news-backfill-2026-11-26.md

## Antigravity Automation Runbook

每日台美四分桶排程的完整 SOP（7 道抓取指令、合併去重、失敗降級、Issue #41 回報）已抽離為專案技能 `.claude/skills/daily-news-notebook/SKILL.md`；本機 `sidecar.json` 只保留排程與權限。以下為單次抓取的通用流程。

1. 執行腳本取得 JSON（例：`uv run python scripts/google_news_digest.py -q "AI" -r TW,US --hours 24 -n 8 --prefer-text --max-chars 6000 -f json`；註：`--no-resolve` 僅供除錯略過還原用）。
2. 若腳本回傳非零結束碼、`articles` 為空或 `errors` 涵蓋全部地區，停止並通知使用者，不建立空筆記本。
3. 呼叫 `gemini-notebook` MCP 的 `create_notebook`，以 `notebook_title`（`YYYY-MM-DD_新聞日報`）建立當天筆記本。
4. 逐筆送入 `create_source`：
   - `delivery == "url"` 且 `resolve_ok == true`：送 `webContent.url = resolved_url`。
   - `delivery == "text"` 且 `excerpt` 非空：送 `textContent`（`mimeType: "text/plain"`），並在正文最前面固定加上出處標頭：
     ```text
     標題：{title}
     媒體：{source}
     地區：{region}
     時間：{published_at}
     來源網址：{resolved_url}

     {excerpt}
     ```
   - 還原或抽取失敗的文章會留在 `errors` 中，不會出現在 `articles`。
5. 呼叫 `list_sources` 檢查狀態；若有 `FAILED` 且腳本或備援抓取有正文，改用含出處標頭的 `textContent` 重送一次。
6. 回報使用者：筆記本名稱與連結、成功筆數、失敗筆數與標題（註：官方 MCP 無刪除 API，舊筆記本需於 NotebookLM 網頁版手動清理）。

返回 [[index]]。
