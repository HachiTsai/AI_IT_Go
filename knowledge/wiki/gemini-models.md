---
title: Gemini 模型可用性（2026-11-14 檢查）
sources:
  - knowledge/raw/gemini-model-check-summary.md
  - knowledge/raw/gemini-model-check-2026-11-25.md
  - knowledge/raw/gemini-model-check-2026-11-25-2.md
updated: 2026-11-25
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

## 維護

> "Drive 上有同名 Google 文件副本，更新任一份時另一份也要同步。" — knowledge/raw/gemini-model-check-summary.md
