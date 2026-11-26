# Google 新聞 RSS 與 Antigravity 結合筆記（2026-11-26）

## 1. Google 新聞抓取機制實測

- Google 新聞沒有官方公開 REST API，但提供免費的官方 RSS Feed。
- 台灣繁體中文頭條端點：`https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant`（2026-11-26 實測回傳 `HTTP/2 200`）。
- 關鍵字搜尋端點：`https://news.google.com/rss/search?q=<keyword>&hl=<hl>&gl=<gl>&ceid=<ceid>`。
- 實測注意事項：Google News `/rss/search` 會對簡易機器人 User-Agent 回傳 `429 Too Many Requests`，改用標準瀏覽器 User-Agent 並搭配請求間隔與退避重試可穩定取得 XML。

## 2. Grok × X 與 Google 新聞 × Antigravity 的定位差異

- Grok + X 的強項是即時社群脈動，適合對話式快報與掌握社群風向。
- Google 新聞 + Antigravity 的強項是跨媒體情報直接接進自動化工作流（Agentic Workflow），結合本地腳本、知識庫與排程。

## 3. 四種結合場景

1. 跨國「新聞溫差」與事實交叉比對：同時抓取 `TW:zh-Hant`、`US:en`、`JP:ja` 等地區 RSS，比對台灣媒體與外媒報導的焦點差異與時間差。
2. 結合本地資料做有脈絡的衝擊分析：抓到產業或技術漏洞新聞後，直接觸發本地分析腳本或比對 `pyproject.toml` 等專案設定。
3. 自動去重並沉澱成可累積的知識庫：對同事件多篇報導進行語意去重與時間軸合併，整理為 Markdown 筆記寫入 `knowledge/wiki/`。
4. 搭配 `/schedule` 排程自動化：定時掃描關鍵字並過濾重複舊聞，產出每日早報或寫入文件。

## 4. 實作工具

- 腳本路徑：`scripts/google_news_digest.py`
- 單元測試：`tests/test_google_news_digest.py`
- 2026-11-26 實機執行 `uv run python scripts/google_news_digest.py -q "AI" -r TW,US --hours 24 -n 5`，成功取得台灣與美國近 24 小時各 5 則 AI 新聞摘要。
