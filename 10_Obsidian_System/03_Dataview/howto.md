> [!more]- 
> ```dataviewjs
 await dv.view("10_Obsidian_System/03_Dataview/Script/device_list", { tag: "#R301 and #Split_Range"})

```dataviewjs
 await dv.view("10_Obsidian_System/03_Dataview/Script/smart_related")
```

---

# 智慧關聯腳本 `smart_related_R301.js` 使用範例

本筆記示範如何在 DataviewJS 區塊中正確呼叫 `smart_related_R301.js` 腳本，以動態顯示相關文件。

## 1. 基本用法 (無參數呼叫)

當您不傳遞任何參數時，`smart_related_R301.js` 會自動使用當前筆記的標籤和資料夾來尋找相關文件。
它會從標籤中排除通用標籤 (`#R301`, `#RCMT_Johor_MLC01`, etc.)，並在預設的 `#R301` 範圍內搜尋。

> [!abstract]- 相關文件 (自動判斷)
> ```dataviewjs
> await dv.view("00_Inbox/00_Dataview/Script/smart_related")
> ```

## 2. 進階用法 (使用 `source` 參數限制搜尋範圍)

如果您希望腳本在更特定的範圍內尋找相關文件，可以使用 `source` 參數。這在您希望只搜尋特定專案、特定標籤或特定資料夾內的關聯文件時非常有用。

### 範例 2.1: 限制搜尋在特定標籤內

假設您只希望搜尋貼有 `#Loop_Analysis` 標籤的相關文件：

> [!abstract]- 相關文件 (限定 `#Loop_Analysis` 範圍)
> ```dataviewjs
> await dv.view("00_Inbox/00_Dataview/Script/smart_related", { source: "#Split_Range" })
> ```

### 範例 2.2: 限制搜尋在特定資料夾內

假設您只希望搜尋 `20_Knowledge_Base/1_Hitachi_EX-N01A` 資料夾內的相關文件：

> [!abstract]- 相關文件 (限定 Hitachi EX-N01A 資料夾範圍)
> ```dataviewjs
> await dv.view("00_Inbox/00_Dataview/Script/smart_related", { source: '"20_Knowledge_Base/1_Hitachi_EX-N01A"' })
> ```

---

### 筆記

* `dv.view()` 函數會執行您指定的 JavaScript 腳本。
* `input` 物件是將參數傳遞給腳本的標準方式。在 `smart_related_R301.js` 中，它會讀取 `input.source`。
* 資料夾路徑需要用雙引號 `"` 包裹，以確保 Dataview 能正確解析含有斜線的路徑。
* `smart_related_R301.js` 內部會自動排除自身文件，並對顯示的標籤進行過濾.

---

# 📋 TASK 查詢語法完整指南

## 🎯 基本概念

`TASK` 查詢會搜尋您的 Obsidian vault 中所有的任務項目（以 `- [ ]` 或 `- [x]` 開頭的項目）。

## 📚 DQL 語法範例

### 1. 基本查詢 - 所有未完成任務

```dataview
TASK
WHERE !completed
```

⚠️ **注意**：是 `completed` 不是 `complete`（有 d 結尾）

### 2. 已完成的任務

```dataview
TASK
WHERE completed
```

### 3. 依截止日期篩選

```dataview
TASK
WHERE !completed AND due
SORT due ASC
```

### 4. 今天到期的任務

```dataview
TASK
WHERE !completed 
AND due = date(today)
```

### 5. 過期的任務

```dataview
TASK
WHERE !completed 
AND due < date(today)
```

### 6. 本週任務

```dataview
TASK
WHERE !completed
AND due >= date(today)
AND due <= date(today) + dur(7 days)
SORT due ASC
```

### 7. 依資料夾篩選

```dataview
TASK
WHERE !completed
AND file.folder != "90_Output"
SORT file.mtime DESC
LIMIT 30
```

### 8. 依標籤篩選

```dataview
TASK
WHERE contains(tags, "#專案A")
AND !completed
```

### 9. 按資料夾分組

```dataview
TASK
WHERE !completed
GROUP BY file.folder
SORT rows.due ASC
```

---

## 🚀 DataviewJS 進階用法

### 何時使用 DataviewJS？

| 情境             | 建議            | 原因                 |
| ---------------- | --------------- | -------------------- |
| **簡單查詢**     | ❌ 用 DQL        | 更簡潔，效能更好     |
| **需要自訂格式** | ✅ 用 DataviewJS | 更多控制權           |
| **複雜邏輯**     | ✅ 用 DataviewJS | 可做條件判斷、計算   |
| **需要統計**     | ✅ 用 DataviewJS | 可顯示數量、百分比等 |

### 範例 1：基本任務列表

```dataviewjs
// 獲取所有未完成的任務
const tasks = dv.pages()
    .file.tasks
    .where(t => !t.completed);

// 渲染任務列表
dv.taskList(tasks, false);
```

### 範例 2：帶統計的儀表板

```dataviewjs
const allTasks = dv.pages().file.tasks;
const pending = allTasks.where(t => !t.completed);
const completed = allTasks.where(t => t.completed);
const overdue = pending.where(t => t.due && t.due < dv.date("today"));

dv.header(3, "📊 任務統計");
dv.paragraph(`
- 總任務數：${allTasks.length}
- 未完成：${pending.length}
- 已完成：${completed.length}
- 過期：${overdue.length}
`);

dv.header(3, "📋 未完成任務");
dv.taskList(pending, false);
```

### 範例 3：自動分類儀表板

```dataviewjs
const allTasks = dv.pages().file.tasks;
const pending = allTasks.where(t => !t.completed);
const today = dv.date("today");

// 分類任務
const overdue = pending.where(t => t.due && t.due < today);
const dueToday = pending.where(t => t.due && t.due.equals(today));
const thisWeek = pending.where(t => t.due && t.due > today && t.due <= today.plus({days: 7}));
const others = pending.where(t => !t.due || t.due > today.plus({days: 7}));

// 統計
dv.header(2, "📊 統計");
dv.paragraph(`
- 總任務：${allTasks.length}
- 未完成：${pending.length}
- 過期：${overdue.length} ⚠️
`);

// 顯示各類任務
if (overdue.length > 0) {
    dv.header(2, "🔴 過期任務");
    dv.taskList(overdue.sort(t => t.due, "asc"), false);
}

if (dueToday.length > 0) {
    dv.header(2, "🟡 今日任務");
    dv.taskList(dueToday, false);
}

if (thisWeek.length > 0) {
    dv.header(2, "🟢 本週任務");
    dv.taskList(thisWeek.sort(t => t.due, "asc"), false);
}

if (others.length > 0) {
    dv.header(2, "📝 其他任務");
    dv.taskList(others.limit(20), false);
}
```

### 範例 4：自訂表格格式

```dataviewjs
const tasks = dv.pages()
    .file.tasks
    .where(t => !t.completed);

// 自訂表格格式
dv.table(
    ["狀態", "任務", "來源", "截止日期"],
    tasks.map(t => [
        t.completed ? "✅" : "⬜",
        t.text,
        t.link,
        t.due || "無"
    ])
);
```

---

## 🎯 TASK 屬性參考

| 屬性         | 說明         | 範例                             |
| ------------ | ------------ | -------------------------------- |
| `completed`  | 是否完成     | `WHERE !completed`               |
| `text`       | 任務文字內容 | `WHERE contains(text, "重要")`   |
| `line`       | 任務所在行號 | `WHERE line > 10`                |
| `file`       | 任務所在檔案 | `WHERE file.name = "專案A"`      |
| `due`        | 截止日期     | `WHERE due < date(today)`        |
| `completion` | 完成日期     | `WHERE completion = date(today)` |
| `link`       | 任務連結     | 用於顯示                         |

---

## 💡 任務格式建議

在筆記中，任務可以這樣寫：

```markdown
- [ ] 完成專案報告 📅 2025-12-15
- [ ] 聯絡客戶 ⏰ 2025-12-10 #重要
- [x] 完成會議記錄 ✅ 2025-12-09
```

Dataview 會自動識別：

* `📅` 或 `due::` 後面的日期作為截止日期
* `✅` 或 `completion::` 後面的日期作為完成日期
* 標籤如 `#重要` 可用於篩選

---

## 🎨 最佳實踐建議

1. **簡單查詢用 DQL**：維護成本低，效能好
2. **複雜邏輯用 DataviewJS**：需要統計、分類、自訂格式時使用
3. **先從 DQL 開始**：等到真的需要更複雜的功能時，再升級到 DataviewJS
4. **使用有意義的標籤和截止日期**：讓查詢更精準。