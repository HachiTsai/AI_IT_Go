# Gemini API 模型定價調查（2026-11-26）

- 調查基準：標準付費層（Standard Paid Tier），匯率參考 `1 USD ≈ 32.87 TWD`
- 單次簡報估算基準：以 2026-11-26 實測新聞簡報為準（Input 約 7,000 tokens、Output + Thoughts 約 5,000 tokens）

## 文字模型定價（每 1M tokens，USD）

- `gemini-2.5-flash-lite`：Input `$0.10` / Output `$0.40`（單次簡報約 NT$ 0.09）
- `gemini-2.5-flash`：Input `$0.30` / Output `$2.50`（單次簡報約 NT$ 0.48）
- `gemini-3.8-flash`：2026-12-31 前優惠價 Input `$0.75` / Output `$3.75`（單次約 NT$ 0.79）；2027-01-01 起為 Input `$1.50` / Output `$7.50`（單次約 NT$ 1.58）
- `gemini-4-hydrogen`：Input `$1.50` / Output `$7.50`（單次簡報約 NT$ 1.58，支援 Google AI Studio Free Tier）
- `gemini-2.5-pro`（<= 200K tokens）：Input `$1.25` / Output `$10.00`（單次簡報約 NT$ 1.93；2026-11-26 實測 6,995 input / 4,919 output+thoughts 為 NT$ 1.90）
- `gemini-4-carbon`：2026-11-30 前優惠價 Input `$2.00` / Output `$10.00`（單次約 NT$ 2.10）；2026-12-01 起調回標準價 Input `$4.00` / Output `$20.00`（單次約 NT$ 4.21，無 Free Tier）
- `gemini-3.1-pro-preview`（<= 200K tokens）：Input `$2.00` / Output `$12.00`（單次簡報約 NT$ 2.43）
- 註：支援 Batch API 的模型通常可享標準價 5 折；`gemini-4-argon` 尚無公開統一零售定價表。

## 影像／Banana 模型定價（每張圖片，USD）

- `gemini-2.5-flash-image`（初代 Nano Banana）：約 `$0.039` / 張（約 NT$ 1.28 / 張，無 Free Tier）
- `gemini-3.1-flash-image`（Nano Banana 新版）：
  - 1K 解析度：約 `$0.033–$0.045` / 張（約 NT$ 1.08–1.48 / 張）
  - 2K 解析度：約 `$0.050` / 張（約 NT$ 1.64 / 張）
  - 4K 解析度：約 `$0.11–$0.15` / 張（約 NT$ 3.62–4.93 / 張）
- 實務建議：製作 Google Slides 簡報時，宜以文字模型整理大綱並透過 Google Slides API 建出可編輯文字框，再搭配 2～3 張 Banana 影像模型配圖，整份圖文簡報總成本約 NT$ 4～5 元。
