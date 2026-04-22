---
tags:
  - Reference
  - Template
  - YAML
type: Documentation
service_name: YAML Schema 規範參考
created: 2025-01-17
---

# YAML Frontmatter 標準化規範 (EX-N01A 知識庫)

> [!abstract] 文件目的
> 本文件定義 `1_Hitachi_EX-N01A` 知識庫中所有 Markdown 檔案的 YAML frontmatter 標準格式，確保知識庫的結構一致性與 Dataview 查詢的可靠性。

---

## 1. 欄位定義總覽

### 1.1 通用欄位 (所有文件類型)

| 欄位名稱 | 類型 | 必填 | 說明 | 範例 |
|:---|:---|:---:|:---|:---|
| `tags` | 列表 | ✅ | 標籤列表 (用於分類與查詢) | `[EX-N01A, DDC]` |
| `type` | 字串 | ✅ | 文件類型 | `DDC`, `SEQ`, `Research` |
| `service_name` | 字串 | ✅ | 服務/功能描述 | `"PRESSURE R301"` |
| `aliases` | 列表 | ⭕ | 別名 (用於快速搜尋) | `[LP017, PICA301]` |
| `created` | 日期 | ⭕ | 建立日期 | `2025-01-17` |
| `updated` | 日期 | ⭕ | 最後更新日期 | `2025-01-17` |
| `status` | 字串 | ⭕ | 文件狀態 | `Draft`, `Complete` |

### 1.2 RCMT 專用欄位 (DDC/SEQ 文件)

| 欄位名稱 | 類型 | 必填 | 說明 | 範例 |
|:---|:---|:---:|:---|:---|
| `factory` | 字串 | ✅ | 廠區名稱 | `Johor` |
| `client` | 字串 | ✅ | 客戶名稱 | `RCMT` |

### 1.3 FNO 功能塊專用欄位

| 欄位名稱 | 類型 | 必填 | 說明 | 範例 |
|:---|:---|:---:|:---|:---|
| `FNO` | 字串 | ✅ | 功能塊編號 | `F00`, `F05` |
| `name` | 字串 | ✅ | 功能塊名稱 | `邏輯演算器` |

---

## 2. Tags 命名規範

### 2.1 標準 Tags 清單

| 類別       | Tag 值                  | 說明                 | 使用場景          |
| :------- | :--------------------- | :----------------- | :------------ |
| **系統**   | `EX-N01A`              | Hitachi EX-N01A 系統 | 所有 EX-N01A 文件 |
| **廠區**   | `RCMT_Johor_MLC01`     | RCMT Johor MLC01   | RCMT 專案文件     |
| **設備區域** | `R301`, `R401`, `R501` | 反應器/儲槽編號           | 設備相關文件        |
| **文件類型** | `DDC`                  | 控制迴路               | DDC 分析文件      |
|          | `SEQ`                  | 順序控制               | SEQ 分析文件      |
|          | `FNO_Block`            | 功能塊定義              | FNO 文件        |
|          | `Research`             | 研究文件               | 研究/分析文件       |
| **分析標記** | `Loop_Analysis`        | 迴路分析               | DDC 文件        |
|          | `SiderAI_SEQ`          | SiderAI 分析         | AI 輔助分析       |
|          | `Deep_Research`        | 深度研究               | 深度分析文件        |
|          | `Reverse_Engineering`  | 逆向工程               | 逆向工程文件        |
| **狀態標記** | `important`            | 重要文件               | 關鍵文件          |
|          | `Dataview`             | Dataview 支援        | 需要查詢的文件       |

### 2.2 Tags 格式規則

> [!warning] 重要規則
>
> 1. **一律使用列表格式** (不使用字串)
> 2. **不使用 `#` 前綴** (Obsidian 會自動處理)
> 3. **使用底線 `_` 分隔單字** (不使用空格)

**正確範例：**
```yaml
tags:
  - RCMT_Johor_MLC01
  - R301
  - DDC
```

**錯誤範例：**
```yaml
tags: "#R301, DDC"  # ❌ 不要使用字串
tags:
  - "#R301"         # ❌ 不要加 # 前綴
  - "Loop Analysis" # ❌ 不要使用空格
```

---

## 3. Type 欄位標準值

| Type 值 | 說明 | 對應 Template |
|:---|:---|:---|
| `Note` | 一般筆記/紀錄 | `20_Note.md` |
| `SURVEY` | 事前調查/現場觀察 | `22_SURVEY.md` |
| `Research` | 事後分析/深度研究 | `23_Research.md` |
| `DDC` | DDC 控制迴路分析 | `20_Note.md` |
| `SEQ` | SEQ 順序控制分析 | `20_Note.md` |
| `FNO_Block` | FNO 功能塊定義 | `20_Note.md` |
| `Experiment` | 實驗報告 | `21_Experiment_Report_Template.md` |

---

## 4. Status 欄位標準值

| Status 值      | 說明  | 建議動作   |
| :------------ | :-- | :----- |
| `Draft`       | 草稿  | 內容尚未完成 |
| `In_Progress` | 進行中 | 正在編輯   |
| `Complete`    | 完成  | 內容已完成  |
| `Verified`    | 已驗證 | 經過驗證確認 |
| `Deprecated`  | 已棄用 | 不再維護   |

---

## 5. Dataview 查詢範例

### 5.1 查詢所有 R301 DDC 迴路

```dataview
TABLE service_name as "Service", aliases as "Aliases", status as "Status"
FROM "20_Knowledge_Base/1_Hitachi_EX-N01A"
WHERE contains(tags, "R301") AND contains(tags, "DDC")
SORT file.name ASC
```

### 5.2 查詢所有 FNO 功能塊

```dataview
TABLE FNO as "FNO", type as "Type", name as "Name"
FROM "20_Knowledge_Base/1_Hitachi_EX-N01A"
WHERE contains(tags, "FNO_Block")
SORT FNO ASC
```

### 5.3 查詢所有進行中的研究

```dataview
TABLE service_name as "Topic", created as "Created", status as "Status"
FROM ""
WHERE contains(tags, "Research") AND status = "In_Progress"
SORT created DESC
```

---

## 6. 修正優先級規劃

### Phase 1: 高優先級 (立即修正)

| 檔案類型 | 數量 | 修正重點 |
|:---|:---:|:---|
| **FNO 功能塊** | ~47 | 統一 `tags`, 補齊 `FNO`, `type`, `name` |
| **RCMT R301 文件** | ~15 | 統一格式，補齊 `created`, `status` |

### Phase 2: 中優先級

| 檔案類型 | 數量 | 修正重點 |
|:---|:---:|:---|
| **RCMT 其他區域** | ~10 | 統一格式 |
| **Roadmap/Research** | ~5 | 補齊欄位 |

### Phase 3: 低優先級

| 檔案類型 | 數量 | 修正重點 |
|:---|:---:|:---|
| **其他文件** | ~10 | 視情況處理 |

---

## 7. 快速參考 (Templater 格式)

### 7.1 事前 SURVEY (調查)

```yaml
---
tags:
  - SURVEY
  - RCMT_Johor_MLC01
type: SURVEY
service_name: ""
aliases: []
factory: Johor
client: RCMT
status: Draft
created: <% tp.file.creation_date() %>
updated: <% tp.date.now("YYYY-MM-DD") %>
---
```

### 7.2 事後 Research (研究)

```yaml
---
tags:
  - Research
  - RCMT_Johor_MLC01
type: Research
service_name: ""
aliases: []
factory: Johor
client: RCMT
status: Draft
created: <% tp.file.creation_date() %>
updated: <% tp.date.now("YYYY-MM-DD") %>
---
```

### 7.3 一般筆記 Note

```yaml
---
tags:
  - Resonac_Johor_MLC01
type: Note
service_name: ""
aliases: []
factory: Johor
client: RCMT
status: Draft
created: <% tp.file.creation_date() %>
updated: <% tp.date.now("YYYY-MM-DD") %>
---
```

---

> [!tip] 維護提醒
> 此規範文件應隨知識庫演進持續更新。如有新的欄位需求，請先更新本文件再實施修改。
