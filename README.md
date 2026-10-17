# AI_IT_Go — AI IT 的修練場

這個 repo 是練習 AI 與 IT 實務的修練場：實驗工具、驗證做法、累積可重複使用的技能（skills）與筆記。

## 目前內容

| 路徑 | 說明 |
| :--- | :--- |
| `.agent/rules/` | 跨 Agent（Antigravity & Claude）模組化規則庫（含 GCP 免費額度、Python 依賴同步、提交流程規範） |
| `.claude/skills/commit-workflow/` | 結構化 Git 提交流程 skill，含 `committer.py`（附敏感檔與依賴同步檢查）與測試 |
| `CLAUDE.md` | 專案規範入口索引（自動引用 `.agent/rules/`） |
| `doc/setup/agy_session.md` | Slack、GCP 與 GitHub 環境與監控完整配置指南 |
| `pyproject.toml` / `requirements.txt` | Python 3.14 依賴設定與工具配置（支援 `uv add`） |
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
