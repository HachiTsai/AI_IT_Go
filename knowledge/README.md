# knowledge/ 第二大腦

- `raw/`：原始來源（剪藏、逐字稿、手寫筆記、原始輸出）。**AI 只讀不改**，由人放入。
- `wiki/`：AI 整理並維護的頁面，每頁需有 front matter（`title`、`sources`、`updated`）。
- 規則見 `.claude/rules/knowledge-base.md`；檢查指令：`python scripts/knowledge_lint.py`。

禁止放入：金鑰、webhook 網址、個人資訊、標記 private 的 Drive 內容。
