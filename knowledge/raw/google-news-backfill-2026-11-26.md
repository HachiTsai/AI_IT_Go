# Google 新聞候選池遞補與 `--prefer-text` 模式（2026-11-26）

- 實測新增被擋網域：`finance.yahoo.com` 會被 NotebookLM 伺服器端回傳 `The source domain is blocked.`，已納入 `BLOCKED_DOMAINS`。
- 候選池遞補（Over-fetch & Backfill）：預設向 RSS 抓取 `limit * 3` 筆候選文章，遇連結還原失敗或被擋網域無法抽正文時標記 `delivery="skip"` 並自動由下一則遞補，確保最終成功筆數。
- `--prefer-text` 模式：本機先抽取所有文章正文改用 `textContent` 送進 NotebookLM，完全避開目標網站封鎖 NotebookLM 雲端爬蟲，抽不到正文者直接淘汰並遞補。
