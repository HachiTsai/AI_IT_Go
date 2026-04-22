---
tags:
  - obsidian
  - syntax
  - Manual
---

---
> [!info]-  相關資訊

---

### 語法

# Markdown Callout 類型大全

| Callout 類型         | 語法範例                            | 預期用途 / 語義                    | 視覺圖標      |
| ------------------ | ------------------------------- | ---------------------------- | --------- |
| NOTE               | > [!NOTE]                       | 普遍的筆記、資訊或一般觀察。               | 📝 筆記圖標   |
| ABSTRACT / SUMMARY | > [!ABSTRACT]  <br>> [!SUMMARY] | 摘要、總結或論文的提綱。                 | 🧾 列表圖標   |
| TIP / HINT         | > [!TIP]  <br>> [!HINT]         | 提示、小技巧、竅門或建議。                | 💡 燈泡圖標   |
| TODO               | > [!TODO]                       | 標註需要執行或完成的待辦事項。              | 📋 待辦圖標   |
| FAQ                | > [!FAQ]                        | 常見問題與解答 (Question & Answer)。 | ❓ 問號圖標    |
| QUOTE              | > [!QUOTE]                      | 引用或引述他人的話語。                  | 💬 語音氣泡圖標 |
| SUCCESS / DONE     | > [!SUCCESS]  <br>> [!DONE]     | 表示某事已成功、完成或確認。               | ✅ 勾選圖標    |
| WARNING / CAUTION  | > [!WARNING]  <br>> [!CAUTION]  | 警告、謹慎操作或潛在風險。                | ⚠️ 警告圖標   |
| ERROR / FAILURE    | > [!ERROR]  <br>> [!FAILURE]    | 錯誤、失敗或重要的負面資訊。               | ❌ 停止圖標    |
| INFO               | > [!INFO]                       | 提供資訊或背景資料。                   | ℹ️ 資訊圖標   |

## 使用範例

> [!NOTE] 這是一個 NOTE 類型的 Callout 範例

> [!WARNING] 這是一個警告類型的 Callout 範例

---

# Markdown Callout 類型大全

## Callout 語法與用途

|顏色|Callout 類型|替代類型|預期用途 / 語義|視覺圖標|語法範例|
|---|---|---|---|---|---|
|藍色|NOTE|-|一般資訊、主要筆記|📝 筆記圖標|> [!NOTE]|
|藍色|INFO|-|背景資料、額外說明|ℹ️ 資訊圖標|> [!INFO]|
|綠色|SUCCESS|DONE, CHECK|完成、成功、確認無誤|✅ 勾選圖標|> [!SUCCESS]|
|綠色|TIP|HINT, IMPORTANT|提示、小技巧、重要建議|💡 燈泡圖標|> [!TIP]|
|灰色|FAQ|QUESTION|常見問答|❓ 問號圖標|> [!FAQ]|
|灰色|ABSTRACT|SUMMARY, TOC|摘要、內容總結、目錄|🧾 列表圖標|> [!ABSTRACT]|
|灰色|QUOTE|CITE|引用語句、引文|💬 語音氣泡圖標|> [!QUOTE]|
|紅色|ERROR|FAILURE|錯誤、失敗、關鍵錯誤|❌ 停止圖標|> [!ERROR]|
|黃色|WARNING|CAUTION, ATTENTION|警告、潛在風險、需要注意|⚠️ 警告圖標|> [!WARNING]|
|橙色|DANGER|CRITICAL|危險、嚴重性高的問題|🚨 警報圖標|> [!DANGER]|
|紫色|BUG|-|軟體錯誤、缺陷|🐛 蟲蟲圖標|> [!BUG]|
|青色|EXAMPLE|-|提供範例或示範|📋 範例圖標|> [!EXAMPLE]|
|青色|SEEALSO|RELATED|相關參考資料|🔗 連結圖標|> [!SEEALSO]|
|粉色|TODO|-|待辦事項|📋 待辦圖標|> [!TODO]|

## 使用範例

> [!NOTE] 這是一個藍色 NOTE 類型的 Callout 範例

> [!WARNING] 這是一個黃色 WARNING 類型的 Callout 範例

> [!SUCCESS] 這是一個綠色 SUCCESS 類型的 Callout 範例

## 自定義 Callout

> [!INFO] 如果輸入的 TYPE 不在列表中，系統會將其渲染為預設顏色（藍色/灰色）