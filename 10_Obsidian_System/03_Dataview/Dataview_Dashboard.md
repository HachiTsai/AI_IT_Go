
# 最近修改過的檔案

> [!abstract]- FIXED
> ```dataview
> TABLE file.mtime as "修改時間"
> FROM ""
> WHERE !contains(file.folder, "00_Inbox")
> AND !contains(file.folder, "10_Obsidian_System")
> SORT file.mtime DESC
> LIMIT 20
> ```
