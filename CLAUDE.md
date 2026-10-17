# AI_IT_Go 開發與環境規範

本專案的所有通用規則統一集中於 `.agent/rules/` 目錄下獨立管理（`.claude/rules` 已透過軟連結同步指向該目錄），Antigravity 與 Claude 皆須嚴格遵守：

- **GCP 永久免費額度規範**：@[.agent/rules/gcp-free-tier.md](.agent/rules/gcp-free-tier.md)
- **Python 環境與套件同步規範**：@[.agent/rules/python-environment.md](.agent/rules/python-environment.md)
- **Git 結構化提交流程規範**：@[.agent/rules/git-commit-workflow.md](.agent/rules/git-commit-workflow.md)

## 擴充規則方式

新增任何通用規則時，請直接於 `.agent/rules/` 下新增獨立的 `<rule-name>.md` 檔案，即可同時對 Antigravity 與 Claude 生效。
