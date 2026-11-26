---
title: 常用工具地圖（備份）
sources: []
updated: 2026-11-25
---

# 常用工具地圖（備份）

線上版是 claude.ai 的 Artifact「常用工具地圖」（頁面加資料庫，可篩選、看板、匯出），本頁是 2026-11-25 的初始資料備份，內容不含任何金鑰或個人資訊。「實測」指實際用過，「推論」是依官方能力整理。

| 工具 | 分類 | 用途 | 狀態 | 依據 | Jira |
| --- | --- | --- | --- | --- | --- |
| Claude Code／MCP | 開發與部署 | 寫程式與測試、開 PR、排程與心跳檢查 | 正常 | 實測 | HAC-18 |
| GitHub | 開發與部署 | 版本控制、PR 與 CI、Actions、issue #23 心跳 | 正常 | 實測 | HAC-23 |
| Vercel | 開發與部署 | 部署網站與預覽環境 | 可連，尚無專案 | 推論 | HAC-26 |
| Atlassian（Jira／Confluence） | 文件與協作 | 新知識與新工具紀錄、文件、白板 | 可讀寫 | 實測 | HAC-19 |
| Google Drive／Docs／Sheets／Slides | 文件與協作 | Drive 儲存與 Docs 摘要，輸出一律用 Google 原生文件 | 可連 | 實測 | HAC-20 |
| Notion | 文件與協作 | 個人筆記，與 Confluence 重疊 | 可連 | 推論 | HAC-24 |
| Slack | 文件與協作 | 自動化通知、搜尋討論 | 可連 | 推論 | HAC-25 |
| Gemini API | AI 與資料 | 模型呼叫、每月重測（見 [[gemini-models]]） | 可連，有每月支出上限 | 實測 | HAC-21 |
| Gemini Notebook (NotebookLM) MCP | AI 與資料 | 建立筆記本與匯入來源（搭配 `scripts/google_news_digest.py`，見 [[google-news-antigravity]]） | 可連（無刪除 API） | 實測 | HAC-32 |
| GCP／BigQuery | AI 與資料 | 資料查詢、免費額度內小型服務（見 [[gcp-free-tier]]） | 部分可用 | 推論 | HAC-22 |
| Figma | 設計 | 設計轉程式碼、Code Connect、FigJam | 可連，權限受限 | 推論 | HAC-17 |
| Canva | 設計 | 簡報、社群圖，不當 Drive 主檔 | 可連 | 推論 | HAC-27 |
| Adobe | 設計 | PDF 處理、影像去背、Express | 可連 | 推論 | HAC-28 |
