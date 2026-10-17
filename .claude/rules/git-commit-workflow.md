# Git 結構化提交流程規範

所有 Git 提交與推送操作一律透過 `.claude/skills/commit-workflow/scripts/committer.py` 執行，並遵循 [`.claude/skills/commit-workflow/SKILL.md`](../../.claude/skills/commit-workflow/SKILL.md) 規範：

## 1. 標準提交步驟

1. **暫存與檢查**：
   ```bash
   python .claude/skills/commit-workflow/scripts/committer.py
   ```
   檢查 staged diff、敏感檔案（`.env`、`*.key`、`credentials/`）與未記錄的 Python 套件依賴。
2. **草擬與提交**：
   將符合模板的 Commit Message 寫入 `.git/COMMIT_MSG_TEMP`，再執行：
   ```bash
   python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage
   ```

## 2. 禁止事項

- 禁止使用 `git commit -m` 傳遞多行訊息，一律使用 `--message-file`（內部呼叫 `git commit -F`）。
- 禁止提交任何明文金鑰、OAuth 憑證或 `.env` 檔案。
- 未經使用者明確同意，禁止執行 `git reset --hard`、`git rebase` 或 `git push --force`。
