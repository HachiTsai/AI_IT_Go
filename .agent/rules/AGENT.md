# Antigravity 專案導引與 `.claude/` 單一真實來源規範

本檔案為 Antigravity 唯一入口規則，旨在將所有專案規則、技能（Skills）與設定統一收斂至 **`.claude/`** 目錄下管理，避免維護兩套重複檔案。

---

## 1. 單一真實來源（Single Source of Truth）鐵律

1. **所有實體設定一律集中於 `.claude/`**：
   - 模組化規則庫統一存放於 `.claude/rules/*.md`。
   - 技能與自動化腳本統一存放於 `.claude/skills/`（如 `.claude/skills/commit-workflow/`）。
2. **採用 Claude Code 官方語法編寫**：
   - 新增或修改任何 Rule、Skill（`SKILL.md`）或設定時，一律遵循 **Claude 官方原生語法與目錄結構**編寫於 `.claude/` 下。
   - 新增 `.claude/rules/<name>.md` 時，必須同步將引用加入根目錄 `CLAUDE.md` 與本檔案（`.agent/rules/AGENT.md`）第 2 節清單中。
3. **先測試、後提交（Test Before Commit）**：
   - 任何程式碼、腳本、依賴或規則變更，在提交前**必須先透過本機 Conda 環境（`ai-it-go`）執行測試與語法檢查**（`pytest` 與 `ruff check .`）。
   - 確認所有測試與檢查通過後，才可透過 `.claude/skills/commit-workflow/scripts/committer.py` 執行結構化 Commit 與 Push。

---

## 2. 專案規則與技能自動載入（指向 `.claude/`）

- **專案總覽入口**：@[CLAUDE.md](../../CLAUDE.md)
- **GCP 永久免費額度規範**：@[.claude/rules/gcp-free-tier.md](../../.claude/rules/gcp-free-tier.md)
- **系統層級 CLI 工具規範**：@[.claude/rules/system-cli-tools.md](../../.claude/rules/system-cli-tools.md)
- **Python 環境與套件同步規範**：@[.claude/rules/python-environment.md](../../.claude/rules/python-environment.md)
- **Git 結構化提交流程規範**：@[.claude/rules/git-commit-workflow.md](../../.claude/rules/git-commit-workflow.md)
- **Git 提交流程 Skill**：@[.claude/skills/commit-workflow/SKILL.md](../../.claude/skills/commit-workflow/SKILL.md)
