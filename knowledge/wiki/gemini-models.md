---
title: Gemini 模型可用性（2026-11-14 檢查）
sources:
  - knowledge/raw/gemini-model-check-summary.md
  - knowledge/raw/gemini-model-check-2026-11-25.md
  - knowledge/raw/gemini-model-check-2026-11-25-2.md
  - knowledge/raw/gemini-pricing-2026-11-26.md
updated: 2026-11-26
---

# Gemini 模型可用性

最近一次檢查在 2026-11-14，結果全數通過；每月重測一次（GitHub Actions，結果回報在 issue #23；Jira HAC-11 已於 2026-11-25 退場）。與 GCP 費用相關的限制見 [[gcp-free-tier]]。

> "測試 23 個文字與影像模型，23 個可用，失敗 0 個。" — knowledge/raw/gemini-model-check-summary.md

## 測試方法

> "文字與影像系列各做一次最小 generateContent 呼叫。" — knowledge/raw/gemini-model-check-summary.md

## 結果摘要

- 文字模型 16 個，全部回覆 OK：Gemini 4、3.x Flash、3.x Lite、3.1 Pro、2.5 系列與兩個 latest 別名。
- 影像模型 7 個，全部回傳 1 張圖片。
- 與 2026-10-14 紀錄中的 6 個模型比較，全部仍可用。

> "金鑰共可見 64 個模型，其中 49 個支援 generateContent。" — knowledge/raw/gemini-model-check-summary.md

## 2026-11-25 重測

> "合計測試 23 個，可用 23 個，失敗 0 個。" — knowledge/raw/gemini-model-check-2026-11-25.md

> "新增可見：`gemini-4-neon`（尚未測試）。" — knowledge/raw/gemini-model-check-2026-11-25.md

> "不再出現：`deep-research-pro-preview-12-2025`。" — knowledge/raw/gemini-model-check-2026-11-25.md

## 2026-11-25 GitHub Actions 實測

每月重測改由 GitHub Actions 執行（每月 25 日），測試方式簡化為只確認有回應。

> "只確認有回應（影像模型不生成圖片，輸出上限 8 tokens）" — knowledge/raw/gemini-model-check-2026-11-25-2.md

> "合計測試 23 個，可用 23 個，失敗 0 個。" — knowledge/raw/gemini-model-check-2026-11-25-2.md

> "新增可見：無。" — knowledge/raw/gemini-model-check-2026-11-25-2.md

## 模型參考定價（2026-11-26 調查）

> "單次簡報估算基準：以 2026-11-26 實測新聞簡報為準（Input 約 7,000 tokens、Output + Thoughts 約 5,000 tokens）" — knowledge/raw/gemini-pricing-2026-11-26.md

- **文字模型（Standard Paid Tier，匯率 `1 USD ≈ 32.87 TWD`）**：
  - `gemini-2.5-flash-lite`：Input `$0.10` / Output `$0.40` per 1M（單次約 NT$ 0.09）
  - `gemini-2.5-flash`：Input `$0.30` / Output `$2.50` per 1M（單次約 NT$ 0.48）
  - `gemini-3.8-flash`：2026-12-31 前優惠 Input `$0.75` / Output `$3.75` per 1M（單次約 NT$ 0.79；2027 起 `$1.50 / $7.50`）
  - `gemini-4-hydrogen`：Input `$1.50` / Output `$7.50` per 1M（單次約 NT$ 1.58）
  - `gemini-2.5-pro`（<= 200K）：Input `$1.25` / Output `$10.00` per 1M（單次約 NT$ 1.93；實測 6,995 / 4,919 tokens 為 NT$ 1.90）
  - `gemini-4-carbon`：2026-11-30 前優惠 Input `$2.00` / Output `$10.00` per 1M（單次約 NT$ 2.10；12/1 起 `$4.00 / $20.00`）
  - `gemini-3.1-pro-preview`（<= 200K）：Input `$2.00` / Output `$12.00` per 1M（單次約 NT$ 2.43）
- **影像／Banana 模型**：
  - `gemini-2.5-flash-image`：約 `$0.039` / 張（約 NT$ 1.28 / 張）
  - `gemini-3.1-flash-image`：1K 約 `$0.033–$0.045`（NT$ 1.08–1.48）、2K 約 `$0.050`（NT$ 1.64）、4K 約 `$0.11–$0.15`（NT$ 3.62–4.93）

> "實務建議：製作 Google Slides 簡報時，宜以文字模型整理大綱並透過 Google Slides API 建出可編輯文字框，再搭配 2～3 張 Banana 影像模型配圖，整份圖文簡報總成本約 NT$ 4～5 元。" — knowledge/raw/gemini-pricing-2026-11-26.md

## 維護

> "Drive 上有同名 Google 文件副本，更新任一份時另一份也要同步。" — knowledge/raw/gemini-model-check-summary.md
