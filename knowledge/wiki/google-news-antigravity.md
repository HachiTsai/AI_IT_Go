---
title: Google 新聞 × Antigravity 結合指南
sources:
  - knowledge/raw/google-news-antigravity-2026-11-26.md
updated: 2026-11-26
---

# Google 新聞 × Antigravity 結合指南

## 核心定位：從「對話式快報」走向「自動化情報流」

與偏重社群即時輿論的 Grok × X 不同，Google 新聞搭配 Antigravity 的核心價值在於將多國媒體報導直接串接進工作區與自動化流程：

> "Google 新聞 + Antigravity 的強項是跨媒體情報直接接進自動化工作流（Agentic Workflow），結合本地腳本、知識庫與排程。" — knowledge/raw/google-news-antigravity-2026-11-26.md

## 資料來源與抓取機制

> "Google 新聞沒有官方公開 REST API，但提供免費的官方 RSS Feed。" — knowledge/raw/google-news-antigravity-2026-11-26.md

實務上需注意搜尋端點的請求標頭限制：

> "Google News `/rss/search` 會對簡易機器人 User-Agent 回傳 `429 Too Many Requests`，改用標準瀏覽器 User-Agent 並搭配請求間隔與退避重試可穩定取得 XML。" — knowledge/raw/google-news-antigravity-2026-11-26.md

## 四種應用場景

1. **跨國「新聞溫差」與事實交叉比對**：同時抓取 `TW:zh-Hant`、`US:en`、`JP:ja` 等多地區 RSS，快速比較台灣媒體與外媒第一手報導的敘事差異與時間差。
2. **結合本地資料做有脈絡的衝擊分析**：抓到產業動態或資安漏洞新聞時，直接連動本地分析腳本或掃描專案依賴（如 `pyproject.toml`）。
3. **自動去重並沉澱為長期知識庫**：對同一事件的多家媒體報導進行標題相似度去重，將重點整理成 Markdown 寫入 `knowledge/wiki/`。
4. **透過 `/schedule` 排程變成背景情報官**：定期掃描指定關鍵字並過濾重複舊聞，自動產出精簡日報。

## 專案內建工具

本專案已提供輕量 CLI 工具 `scripts/google_news_digest.py`（測試於 `tests/test_google_news_digest.py`）：

```bash
# 抓台灣與美國最近 24 小時的「AI」新聞，各取前 5 則
uv run python scripts/google_news_digest.py -q "AI" -r TW,US --hours 24 -n 5

# 輸出 JSON 供其他腳本或 Agent 串接
uv run python scripts/google_news_digest.py -q "台積電" -r TW,JP -f json
```

返回 [[index]]。
