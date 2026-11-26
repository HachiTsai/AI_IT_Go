"""study-notes 技能的模組化函式庫。

- common：共用工具（檔名清理、repo 偵測、frontmatter、gdrive CLI 尋找）
- base / local_backend：儲存後端介面與本機後端（不需任何雲端依賴）
- drive_backend：gdrive CLI 後端（只有真的要進 Drive 時才會被匯入）
- mermaid：Mermaid 區塊擷取、檢查與（選用）轉圖
"""
