# 知識庫（knowledge/）作業規範

## 1. 結構

- `knowledge/raw/`：原始來源。2026-11-25 起 hachi 授權 Claude 可新增與維護（不再由 `.claude/settings.json` 限制）；仍須遵守下列界線：
  - 只放整理過、不含敏感資訊的來源；不得放金鑰、webhook 網址、個人資訊或 private 資料夾內容。
  - 已存在的來源檔，修改或刪除前須取得 hachi 同意（避免悄悄改寫 wiki 引用的原文）。
  - 一律經 PR 與 CI 提交，不直接 push 到 `main`。
- `knowledge/wiki/`：Agent 整理並維護的頁面；一檔一主題，檔名小寫加連字號（如 `tax-policy.md`）。
- 原 `doc/` 已移入 `knowledge/wiki/`，不再保留。

## 2. wiki 頁面格式

- 開頭 front matter 必須有 `title`、`sources`（列出 `knowledge/raw/` 下實際存在的檔案）、`updated`。
- `[[page-name]]` 連結必須對應 `knowledge/wiki/page-name.md`。
- 重要事實以引用行標示出處：`> "原文句子" — knowledge/raw/檔名.md`，句子必須逐字存在於該原始檔。
- 不得殘留 `TODO`。

## 3. 檢查

修改 `knowledge/wiki/` 後執行 `python scripts/knowledge_lint.py`，有問題先修正再提交。

## 4. 安全

- 嚴禁將金鑰、webhook 網址、個人資訊寫入 `knowledge/`（會被 git 追蹤）。
- 不得匯入標記 private 的 Drive 資料夾內容。
