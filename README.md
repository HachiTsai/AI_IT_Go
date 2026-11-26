# AI_IT_Go — AI IT 的修練場

這個 repo 是練習 AI 與 IT 實務的修練場：實驗工具、驗證做法、累積可重複使用的技能（skills）與筆記。

## 目前內容

| 路徑 | 說明 |
| :--- | :--- |
| `.claude/rules/` | 唯一真實來源之模組化規則庫（含 GCP 免費額度、CLI 工具、Python 依賴同步、提交流程規範） |
| `.claude/skills/commit-workflow/` | 結構化 Git 提交流程 skill，含 `committer.py`（附敏感檔、依賴與規則索引同步檢查）與測試 |
| `AGENTS.md` | Antigravity 轉接入口，指向 `CLAUDE.md`（規則索引唯一維護處）並提醒先測試後提交 |
| `CLAUDE.md` | Claude 專案規範入口索引（自動引用 `.claude/rules/`） |
| `knowledge/wiki/agy-session.md` | Slack、GCP 與 GitHub 環境與監控完整配置指南 |
| `knowledge/wiki/google-news-antigravity.md` | Google 新聞 RSS × NotebookLM 零費用自動化指南與 Runbook |
| `pyproject.toml` | Python 3.14 單一依賴來源與工具配置（與 `.claude/rules/python-environment.md` 同步） |
| `scripts/google_news_digest.py` | 多國 Google News RSS 抓取、去重、原始網址還原與正文備援工具 |
| `scripts/init.sh` | 專案環境自動初始化腳本（GCP 認證與 `.venv` 建置） |

## 使用方式

### 提交流程

```bash
# 暫存並印出 diff 與模板，供草擬 Commit Message
python .claude/skills/commit-workflow/scripts/committer.py

# 提交已草擬好的訊息並推送
python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage

# 小型變更：自動產生精簡訊息並提交
python .claude/skills/commit-workflow/scripts/committer.py --auto-quick
```

參數與規範見 [`SKILL.md`](.claude/skills/commit-workflow/SKILL.md)。

### 執行測試

```bash
pip install pytest
python -m pytest .claude/skills/commit-workflow/scripts/tests
```

### 新聞自動化（Google News RSS → NotebookLM）

零 API 費用流程：由腳本抓取並還原真實媒體網址，再透過 `gemini-notebook` MCP 送入 NotebookLM 進行摘要與跨國溫差分析（完整 Runbook 見 [google-news-antigravity.md](knowledge/wiki/google-news-antigravity.md)）。

```bash
# 抓取台灣與美國近 24 小時「AI」新聞（各 5 則），輸出結構化 JSON
uv run python scripts/google_news_digest.py -q "AI" -r TW,US --hours 24 -n 5 -f json
```
