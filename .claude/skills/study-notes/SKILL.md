---
name: study-notes
description: 跨專案通用學習筆記技能，支援本機與雲端環境自動同步至 Google Drive 的 Agent_Study_Notes 目錄，且一律採用 Google 原生文件格式 (Google Docs 📄、Sheets 📊、Slides 📽️)。
type: prompt
whenToUse: 當使用者要求記錄學習心得、技術踩坑、架構決策、除錯排錯筆記，或要求查詢/回顧歷史筆記時調用。
disableModelInvocation: false
metadata:
  version: "1.1.0"
  folder_id: "1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn"
---

# Study Notes Skill (跨專案通用學習筆記 - Google Workspace 原生格式版)

本技能提供標準化的學習筆記沉澱與檢索工作流，直接連接至 Google Drive 的 `00_Claude/Agent_Study_Notes/` 目錄，**所有儲存至 Google Drive 的檔案一律採用 Google 原生文件格式（Google Docs 📄, Sheets 📊, Slides 📽️）**。

## 📋 存放路徑與架構規範

- **雲端 Google Drive Folder ID**：
  `1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn`
- **儲存後端選擇**：
  - 有 gdrive CLI（可用 `GDRIVE_BIN` 指定）：直接建立 Google 原生文件到 Drive。
  - 沒有 gdrive CLI：只存到本機暫存 `~/.cache/agent_study_notes/`，不會同步到 Drive，並會顯示警告。
  - 若要寫到本機同步資料夾，需明確設定 `AGENT_STUDY_NOTES_DIR`（注意：這樣寫入的是 `.md` 純文字，不是 Google 文件）。
- **檔案格式鐵律**：
  - **預設一律採用 Google Docs (Google 文件 📄)**，禁止直接在雲端留存未轉換的裸 `.md` 文字檔。
  - 支援 Google Sheets (Google 試算表 📊，適用結構化數據與統計)。
  - 支援 Google Slides (Google 簡報 📽️，適用投影片大綱)。
- **目錄結構**：
  `Agent_Study_Notes/<repo名>/<類別>_<標題>` (Google 文件)

---

## 🛠️ 常用指令

腳本位置：`.claude/skills/study-notes/scripts/note.py`

### 1. 新增筆記 (預設自動建立 Google 文件 📄)
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Firmware" \
  --title "ESP32_Flashing_Guide" \
  --tags "esp32,flashing,pio" \
  --content "## 📌 核心摘要\n...\n## 🛠️ 排錯步驟\n..."
```

- 上傳 Drive 失敗時 `add` 以 exit 1 結束，錯誤寫到 stderr，並列出保留待上傳內容的暫存檔路徑。
- 找不到也建不出 repo 子資料夾（拿不到資料夾 ID）時，`add`、帶 `--repo` 的 `list`／`read` 以 exit 1 結束，不會改用根目錄。

- 從檔案讀取長篇 Markdown 內容並轉為 Google 文件：
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Architecture" \
  --title "SSOT_Pattern" \
  --content-file <path_to_markdown>
```

- 建立 Google 試算表 📊（以 CSV 內容建立）：
```bash
python3 .claude/skills/study-notes/scripts/note.py add \
  --category "Metrics" \
  --title "Latency_Benchmark" \
  --format sheet \
  --content "Time,Ping_ms,RSSI\n10:00,4.2,-65\n10:01,3.8,-64"
```

### 2. 檢索筆記 (Search)
```bash
python3 .claude/skills/study-notes/scripts/note.py search "Flashing"
```

### 3. 讀取筆記 (Read - 自動從 Google Doc 匯出為 Markdown 輸出)
```bash
python3 .claude/skills/study-notes/scripts/note.py read "ESP32_Flashing_Guide"
```

### 4. 列出目錄現有筆記 (List)
```bash
python3 .claude/skills/study-notes/scripts/note.py list
```

---

### 5. Mermaid 圖表
筆記內文可直接寫 ```` ```mermaid ```` 區塊。2026-11-26 實測 Google 文件的行為：
- 不會渲染成圖：匯入後變成原生程式碼區塊（語言「None」，語言清單沒有 Mermaid）。
- 原始碼完整保留，`read` 匯出 md 時內容不變，但 `mermaid` 標籤會丟失，只剩無語言的圍欄；`mermaid check` 會把「第一行是已知圖表宣告的無標籤圍欄」也當成 Mermaid 檢查。
- 要看到圖：用 GitHub（repo 的 wiki／README 會直接渲染），或用下方轉圖指令產生圖檔。

```bash
# 檢查（不需要 Drive）：圍欄未閉合、空區塊、第一行不是已知圖表宣告、括號不成對
python3 .claude/skills/study-notes/scripts/note.py mermaid check path/to/note.md

# 轉圖檔（選用，需自行安裝 mermaid-cli：npm install -g @mermaid-js/mermaid-cli）
python3 .claude/skills/study-notes/scripts/note.py mermaid render path/to/note.md --out /tmp/diagrams --format png

# 轉圖並內嵌成 HTML（base64 圖片；Drive 把 HTML 轉成 Google 文件時圖片會保留）
python3 .claude/skills/study-notes/scripts/note.py mermaid embed path/to/note.md --out /tmp/note.html

# 直接存成帶圖的 Google 文件（Drive 後端；轉圖失敗就中止，不會存成沒圖的版本）
python3 .claude/skills/study-notes/scripts/note.py add -c Tools -t Title --content-file note.md --mermaid-mode image
```

轉圖環境：`mmdc` 用 `MMDC_BIN` 指定路徑（預設找 PATH）；容器內若有 `/opt/pw-browsers/chromium` 會自動以它執行並關閉沙箱，其他位置用 `MERMAID_CHROME_PATH`。圖依尺寸縮放到最寬 620、最高 700 像素。

實測（2026-11-26，Drive 連接器）：base64 內嵌的 HTML 轉成 Google 文件後，圖片確實嵌在文件裡（匯出 docx 內有 media）。`--mermaid-mode image` 在 gdrive CLI 後端上傳 HTML 的路徑只做過單元測試（mock），尚未用真實 gdrive CLI 驗證；沒有 Drive 後端時只存 Markdown 並警告。

`add` 預設會在存檔前檢查 Mermaid 區塊並以警告提示；加 `--mermaid-strict` 則有問題就中止。

## 🧩 腳本模組結構

入口 `scripts/note.py` 只負責 CLI 與選擇後端，實作在 `scripts/notelib/`：

| 模組 | 內容 |
| :--- | :--- |
| `common.py` | 檔名清理、repo 偵測、frontmatter、找 gdrive CLI（不依賴雲端） |
| `base.py` / `local_backend.py` | 後端介面與本機 Markdown 後端 |
| `drive_backend.py` | gdrive CLI 後端，只有偵測到 gdrive CLI 要進 Drive 時才匯入 |
| `mermaid.py` | Mermaid 區塊擷取、檢查、轉圖、內嵌圖片 |
| `html_export.py` | Markdown 轉 HTML（含內嵌圖片），供 Drive 轉成 Google 文件 |

`mermaid` 子指令與本機後端完全不載入 Drive 模組。測試在 `scripts/tests/`，已納入 `pytest` 的 `testpaths`。

---

## 📝 筆記格式標準 (Frontmatter + Markdown)

每份筆記自動產生標準 YAML Frontmatter，上傳時 Google Drive 會自動將 Markdown 標題、清單、表格解析為原生 Google 文件版面：

```markdown
---
title: "筆記標題"
repo: "當前專案名稱"
category: "技術分類"
date: YYYY-MM-DD
tags: ["tag1", "tag2"]
---

# 標題

## 📌 核心摘要 (TL;DR)
- 簡要說明問題、決策或學習核心。

## 🔍 問題背景與原理探討
- 詳細記錄當時的情境、錯誤現象與根因分析。

## 🛠️ 最佳實踐與排錯手冊
- 具體指令、設定檔範例、架構圖或程式碼片段。
```
