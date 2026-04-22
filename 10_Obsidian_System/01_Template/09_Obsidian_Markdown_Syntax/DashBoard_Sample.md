---
tags:
  - "#排除條件"
aliases:
status: pending
---

> [!note]- 💡 為什麼用 `!contains()` 而不是 `!=`？
>
> - `file.folder != "90_Sandbox"` → 只排除路徑**完全是** `90_Sandbox` 的檔案
> - `!contains(file.folder, "90_Sandbox")` → 排除路徑中**包含** `90_Sandbox` 的所有檔案（含子資料夾）✅

---

> [!tip]- 💡 排除邏輯說明
> 
> ## ⚠️ 常見錯誤：排除時使用 OR
> 
> ### ❌ 錯誤寫法
>
> ```dataview
> AND (
>     file.folder != "A" OR file.folder != "B"
> )
> ```
> 
> **問題**：使用 `OR` 會讓所有任務都通過！
>
> - 假設任務在資料夾 A
> - `file.folder != "A"` → ❌ False
> - `file.folder != "B"` → ✅ True（因為它不在 B）
> - 結果：條件為 True，任務仍會顯示
> 
> ---
> 
> ### ✅ 正確寫法
>
> ```dataview
> AND file.folder != "A"
> AND file.folder != "B"
> ```
> 
> **效果**：只有**不在 A 且不在 B** 的任務才會顯示
> 
> ---
> 
> ## 🎯 邏輯對照表
> 
> | 需求 | 運算符 | 範例 |
> |------|--------|------|
> | **排除多個資料夾** | `AND` | `folder != "A" AND folder != "B"` |
> | **白名單多個資料夾** | `OR` | `folder = "A" OR folder = "B"` |
> | **排除多個標籤** | `AND` | `!contains(tags, "#A") AND !contains(tags, "#B")` |
> | **白名單多個標籤** | `OR` | `contains(tags, "#A") OR contains(tags, "#B")` |
> 
> ---
> 
> ## 💡 記憶口訣
> 
> - **排除用 AND**：「不要 A **且** 不要 B」
> - **白名單用 OR**：「要 A **或** 要 B」
