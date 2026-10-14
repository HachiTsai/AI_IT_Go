# AI_IT_Go — AI IT 的修練場

這個 repo 是練習 AI 與 IT 實務的修練場：實驗工具、驗證做法、累積可重複使用的技能（skills）與筆記。

## 目前內容

| 路徑 | 說明 |
| :--- | :--- |
| `.claude/skills/commit-workflow/` | 結構化 Git 提交流程 skill，含 `committer.py` 與測試 |

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
