# AGENTS.md — Antigravity / 通用 Agent 入口

本檔是轉接入口，**所有規則與技能的唯一真實來源是 `.claude/`，完整索引在 `CLAUDE.md`**。下列重點與規則摘要已內嵌於此，不讀其他檔案也能掌握全貌；細節與最新內容以各規則檔為準。

- **專案總覽與規則索引**：@[CLAUDE.md](CLAUDE.md)

## 必守重點

1. 變更先通過 `pytest` 與 `ruff check .`，再用 `.claude/skills/commit-workflow/scripts/committer.py` 提交與推送。
2. 一律在分支上開 PR 向 `main`，禁止直接 push `main`；CI 全綠後採 Merge Commit。
3. 新增規則或技能時，更新 `CLAUDE.md` 的引用清單，並在本檔「規則摘要」補一行（`committer.py` 會檢查）。
4. 嚴禁將金鑰、webhook 網址、個人資訊寫入 git。
5. Jira（HAC）只記「新知識擴展」與「新工具加入」（工具歸 Epic HAC-16）；一般任務由 PR、CI 與 GitHub issue 追蹤，不另開卡。

## 規則摘要（`.claude/rules/`）

- [gcp-free-tier.md](.claude/rules/gcp-free-tier.md)：GCP 一律走永久免費額度，區域預設 `us-central1`，Cloud Run／Functions 設 `--max-instances=1`，付費服務先告知再執行。
- [system-cli-tools.md](.claude/rules/system-cli-tools.md)：系統層級 CLI 工具清單、路徑與安裝指令（`gcloud`、`gh`、`uv`、`rg`、`fd` 等）。
- [python-environment.md](.claude/rules/python-environment.md)：以 `pyproject.toml` 為唯一依賴來源，新增套件須同步更新該規則檔內的 toml 區塊。
- [git-commit-workflow.md](.claude/rules/git-commit-workflow.md)：提交一律用 `committer.py --message-file`，不手動 `git commit -m`；PR 經 CI 全綠後以 Merge Commit 合併。
- [knowledge-base.md](.claude/rules/knowledge-base.md)：`knowledge/wiki/` 頁面需 front matter 與逐字引用，修改後跑 `python scripts/knowledge_lint.py`；`knowledge/raw/` 只放無敏感資訊的來源，改既有檔須先經 hachi 同意。
