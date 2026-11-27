---
name: daily-news-notebook
description: 每日台美四分桶新聞自動化工作流：以 google_news_digest.py 抓取頭條／政策／總經／產業四桶新聞，合併去重後透過 gemini-notebook MCP 匯入當天 NotebookLM 筆記本，並在 Issue #41 回報執行結果。
whenToUse: 排程（本機 Antigravity sidecar.json 每日 08:30 台北時間）觸發，或使用者在對話中說「跑今天的新聞日報」「補跑新聞筆記本」「執行 daily-news-notebook」時調用。
disableModelInvocation: false
metadata:
  version: "2026.11.27"
---

# Daily News Notebook Skill（每日台美四分桶新聞 → NotebookLM）

本技能是每日新聞自動化流程的唯一 SOP 來源。本機 `sidecar.json` 只負責排程與權限白名單，工作流內容一律以本檔為準，修改須經分支與 PR。

背景與設計脈絡：[`knowledge/wiki/google-news-antigravity.md`](../../../knowledge/wiki/google-news-antigravity.md)、Issue #40、#41、#45。

## 目標

每日建立一本 `YYYY-MM-DD_新聞日報` 筆記本，收錄 **50 則以上唯一新聞**（依 `resolved_url` 去重），涵蓋台灣（TW）與美國（US）四個分桶。

## 前置條件

- 在 repo 根目錄執行（指令使用相對路徑 `scripts/google_news_digest.py`）。
- 可用 `uv`；`gemini-notebook` MCP 已連線（需 `create_notebook`、`create_source`、`list_sources`）。
- 可用 `gh` 並有權在 `HachiTsai/AI_IT_Go` 留言（回報 Issue #41）。

## 步驟 1：抓取四分桶 JSON（7 道指令）

所有指令皆帶 `--prefer-text --max-chars 6000 -f json`：本機先抽正文，抽不到足夠正文者淘汰並自動遞補。

| 分桶 | 地區 | 指令 |
| :--- | :--- | :--- |
| 桶1 頭條 | TW,US | `uv run python scripts/google_news_digest.py -r TW,US --hours 24 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶2 政策 | TW | `uv run python scripts/google_news_digest.py -q '"央行" OR "金管會" OR "經濟部" OR "國發會" OR "關稅" OR "補貼" OR "新制"' -r TW --hours 48 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶2 政策 | US | `uv run python scripts/google_news_digest.py -q '"Fed" OR "Federal Reserve" OR "Treasury" OR "White House" OR "tariff" OR "SEC" OR "regulation"' -r US --hours 48 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶3 總經 | TW | `uv run python scripts/google_news_digest.py -q '"CPI" OR "GDP" OR "PMI" OR "景氣燈號" OR "出口" OR "通膨" OR "利率"' -r TW --hours 48 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶3 總經 | US | `uv run python scripts/google_news_digest.py -q '"CPI" OR "PCE" OR "GDP" OR "nonfarm payrolls" OR "unemployment" OR "inflation" OR "rate cut"' -r US --hours 48 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶4 產業 | TW | `uv run python scripts/google_news_digest.py -q '"AI" OR "半導體" OR "台積電" OR "法說會" OR "財報" OR "比特幣"' -r TW --hours 24 -n 8 --prefer-text --max-chars 6000 -f json` |
| 桶4 產業 | US | `uv run python scripts/google_news_digest.py -q '"AI" OR "semiconductor" OR "Nvidia" OR "earnings" OR "Bitcoin" OR "crypto"' -r US --hours 24 -n 8 --prefer-text --max-chars 6000 -f json` |

每道指令輸出 `{generated_at, notebook_title, articles, errors}`；每篇文章含 `region`、`title`、`source`、`published_at`、`resolved_url`、`resolve_ok`、`delivery`、`excerpt`。

## 步驟 2：合併、去重與失敗降級

1. 單一指令失敗（非零結束碼，或該桶 `articles` 為空）時：**略過該桶**，記下分桶名稱與 `errors` 前幾筆，其餘桶照常處理。
2. 依上表順序合併各桶 `articles`，以 `resolved_url` 去重，**保留第一筆**（避免跨桶重複）。
3. 只有在 **7 道指令全數失敗** 或 **合併後總數為 0** 時才停止：不建立空筆記本，將錯誤摘要留言到 Issue #41（格式見步驟 6）。

## 步驟 3：建立筆記本

使用 JSON 中的 `notebook_title`（`YYYY-MM-DD_新聞日報`，取執行當天日期）呼叫 `gemini-notebook` 的 `create_notebook`。

## 步驟 4：逐筆匯入來源（`create_source`）

- `delivery == "text"` 且 `excerpt` 非空：以 `textContent`（`mimeType: "text/plain"`）送出。
  - `displayName` 加分桶與地區前綴，例如 `[政策-TW] 標題 - 來源`（前綴用 `頭條`／`政策`／`總經`／`產業`）。
  - 內文開頭固定附上出處標頭：

    ```text
    標題：{title}
    媒體：{source}
    地區：{region}
    時間：{published_at}
    來源網址：{resolved_url}

    {excerpt}
    ```

- `delivery == "url"` 且 `resolve_ok == true`：以 `webContent.url = resolved_url` 送出。
- 其他情況不送出（還原或抽取失敗的文章已留在 `errors`）。

## 步驟 5：檢查最終狀態

呼叫 `gemini-notebook` 的 `list_sources`（帶 `pageSize: 100`），統計 `ACTIVE` 與 `FAILED` 數量。

## 步驟 6：回報 Issue #41（必做）

執行結束後，用 `gh issue comment 41 --repo HachiTsai/AI_IT_Go --body-file <檔案>` 留下一則當天回報，並在對話中輸出相同摘要。留言至少包含：

- 筆記本名稱、NotebookLM 連結、來源數（送出總筆數）
- `ACTIVE` / `FAILED` 數量
- errors 摘要：
  - 各分桶是否觸發大量 429
  - 是否有 Reuters 缺漏（說明實得筆數，以及 `errors` 是否出現 Reuters）
  - 失敗分桶或代表性錯誤前幾筆

**嚴禁**在留言中包含任何金鑰、webhook 網址或個人資訊（如 Email、帳號名稱）。

## 手動觸發與補跑

- 使用者在對話中要求時，可直接照本檔步驟 1～6 執行，不必等排程。
- `notebook_title` 一律取執行當天日期；補跑前一天時，請在 Issue #41 回報中註明「補跑」與原本應執行的日期。
- 官方 MCP 沒有刪除 API；重跑造成的重複筆記本需在 NotebookLM 網頁版手動清理。

## 本機排程（`sidecar.json`，不入 git）

`sidecar.json` 只保留：

- 排程：`CRON_TZ=Asia/Taipei 30 8 * * *`
- `restart_policy`: `"always"`
- `agent_permissions.access_grants`：
  - `command(uv run python <workspace>/scripts/google_news_digest.py)`
  - `command(gh issue comment)`
  - `mcp(gemini-notebook/create_notebook)`
  - `mcp(gemini-notebook/create_source)`
  - `mcp(gemini-notebook/list_sources)`

排程提示詞只需一句話指向本技能，例如：

```text
在 AI_IT_Go repo 根目錄，依 .claude/skills/daily-news-notebook/SKILL.md 執行今天的每日台美四分桶新聞流程（步驟 1～6），並在 Issue #41 回報。
```

## 變更紀錄

- **2026.11.27**：自本機 `sidecar.json` 長提示詞抽離為專案 Skill（Issue #45），內容與原排程 SOP 一致，新增手動補跑說明。
