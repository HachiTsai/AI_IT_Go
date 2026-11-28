# 專案提示、開 PR 與 issue 附圖規範

本規則把 Claude 雲端專案的提示（只存在 Claude 專案設定，Antigravity 看不到）與開 PR 慣例寫進 repo，讓兩邊 Agent 共用。

## 1. 專案提示（標準作業）

1. **開新 session 先安全同步**：先執行 `git pull --ff-only`（或 `committer.py --sync`），只做 fast-forward。
2. **Drive 資料夾輪詢**：嚴禁進入標記「no open」的資料夾。
3. **嚴禁敏感資訊入庫**：金鑰、webhook 網址、個人資訊不得寫入 git 追蹤的檔案。

## 2. 開 PR 流程

1. 在指定分支提交（用 `committer.py`），向 `main` 開 PR，**一律先開草稿（draft）**。
2. PR 內文開頭若專案設定提供了署名區塊（`claude-projects-attribution` 註解與「Requested by」那一行），原樣放在最前面，編輯時不得刪除。
3. 開 PR 後：把 `HachiTsai` 設為 assignee，再另外一次呼叫請求其 review（兩步各自獨立，失敗就略過）。若 PR 作者本人就是 `HachiTsai`，GitHub 不允許對自己請求 review，略過即可。
4. 開完 PR 後訂閱其活動（CI、review）。`claude/*`、`agy/*` 分支由 CI 的 `auto-merge` 自動合併；其他分支在 CI 全綠且無衝突後依 `git-commit-workflow.md` 以 Merge Commit 合併。
5. 只為測試或實驗而開的 PR，分支不用 `claude/`、`agy/` 前綴（否則會被自動合併），結束後依 hachi 指示關閉，不主動刪遠端分支。

## 3. 問題截圖與 issue 附圖（2026-11-25 實測）

實測結論：GitHub REST API 不能上傳 issue 附件；外部圖片網址在 Claude Code 送出時會被改成一般連結；圖片 commit 進 repo 浪費空間。因此採「存 Drive、issue 貼連結」：

1. 截圖後縮小（約 10 KB 以內；以內嵌 base64 上傳，太大會失敗），先確認沒有金鑰或個人資訊。
2. 存到 Drive 資料夾 `tmp/screenshot`（id `18FoBJh30Pb9jiYeFMEES13m8uotUpRYs`）。
3. 在 issue 貼 Drive 檢視連結，並用一句話說明圖在看什麼。issue 內只會顯示連結，不會顯示圖片。
4. 不要把截圖 commit 進 repo，也不要在 issue 使用外部圖片語法。
