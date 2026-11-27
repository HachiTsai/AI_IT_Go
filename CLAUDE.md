# AI_IT_Go 開發與環境規範

本專案以 `.claude/` 為唯一真實來源（Single Source of Truth），所有通用規則與技能皆採用 Claude 官方語法集中於 `.claude/rules/` 與 `.claude/skills/` 管理（Antigravity 則透過根目錄 `AGENTS.md` 轉接至本檔）：

- **GCP 永久免費額度規範**：@[.claude/rules/gcp-free-tier.md](.claude/rules/gcp-free-tier.md)
- **系統層級 CLI 工具規範**：@[.claude/rules/system-cli-tools.md](.claude/rules/system-cli-tools.md)
- **Python 環境與套件同步規範**：@[.claude/rules/python-environment.md](.claude/rules/python-environment.md)
- **Git 結構化提交流程規範**：@[.claude/rules/git-commit-workflow.md](.claude/rules/git-commit-workflow.md)
- **知識庫（knowledge/）作業規範**：@[.claude/rules/knowledge-base.md](.claude/rules/knowledge-base.md)
- **專案提示、開 PR 與 issue 附圖規範**：@[.claude/rules/project-workflow.md](.claude/rules/project-workflow.md)
- **跨專案通用學習筆記技能**：@[.claude/skills/study-notes/SKILL.md](.claude/skills/study-notes/SKILL.md)
- **每日台美新聞 NotebookLM 工作流技能**：@[.claude/skills/daily-news-notebook/SKILL.md](.claude/skills/daily-news-notebook/SKILL.md)

## 開發、擴充與提交鐵律

1. **擴充規則與技能**：新增任何規則或技能時，請以 Claude 官方語法直接建立於 `.claude/rules/<rule-name>.md` 或 `.claude/skills/<skill-name>/`，並同步更新本檔的引用清單（`AGENTS.md` 只指向本檔，不維護清單）。
2. **測試通過主動使用技能自動 Commit**：任何變更必須先通過 `pytest` 與 `ruff check .` 驗證無誤；完成後 Agent 必須主動使用 `.claude/skills/commit-workflow/scripts/committer.py` 執行結構化 Commit 與 Push，嚴禁使用未經驗證的手動提交，無需等待使用者口令。
3. **分支與 PR 鐵律**：所有變更一律在指定的分支上進行並向 `main` 發起 Pull Request，禁止直接 push 到 `main` 分支；GitHub Actions CI 全綠後採 Merge Commit 合併。

