# AGENTS.md — Antigravity / 通用 Agent 入口

本檔只是轉接入口，**所有規則與技能的唯一真實來源是 `.claude/`，索引在 `CLAUDE.md`**。開工前請先完整讀取並遵守：

- **專案總覽與規則索引**：@[CLAUDE.md](CLAUDE.md)

## 必守重點（細節以 CLAUDE.md 與 `.claude/rules/` 為準）

1. 變更先通過 `pytest` 與 `ruff check .`，再用 `.claude/skills/commit-workflow/scripts/committer.py` 提交與推送。
2. 一律在分支上開 PR 向 `main`，禁止直接 push `main`；CI 全綠後採 Merge Commit。
3. 新增規則或技能時只更新 `CLAUDE.md` 的引用清單（本檔不需要維護清單）。
4. 嚴禁將金鑰、webhook 網址、個人資訊寫入 git。
5. Jira（HAC）卡片規則見專案指示：完成工作要在對應卡留言或轉狀態，PR 標題帶卡號。
