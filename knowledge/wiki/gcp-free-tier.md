---
title: GCP 永久免費額度作業規格
sources:
  - knowledge/raw/gcp-free-tier-spec.md
  - knowledge/raw/gcp-free-tier-audit-2026-11-25.md
updated: 2026-11-25
---

# GCP 永久免費額度作業規格

本頁是專案採用的作業上限；官方額度可能調整，使用前請對照官方頁面。模型相關資訊見 [[gemini-models]]。

## 區域

> "首選：us-central1" — knowledge/raw/gcp-free-tier-spec.md

次選為 us-east1 與 us-west1；未經明確指示不部署到亞洲區域，服務集中在同一區域以避免跨區網路費用。

## 重點上限

- Cloud Functions 與 Cloud Run：region 為 us-central1、max-instances 為 1、memory 為 256Mi，事件觸發不啟用無限重試。
- Compute Engine：僅 e2-micro，boot disk 用 pd-standard 且 30 GB 以內。
- Cloud Storage：單一區域 STANDARD，合計 5 GB 以內，禁用 Multi-region。
- Artifact Registry：500 MB 以內。
- Secret Manager：有效版本 6 個以內。
- Pub/Sub：每月前 10 GB 免費。

## 2026-11-25 對照檢查

> "不符：規格要求 max-instances 為 1" — knowledge/raw/gcp-free-tier-audit-2026-11-25.md

目前唯一的函式 billing-to-slack 實例上限為 100，已不符規格；其餘可驗證項目符合。

> "服務帳號權限不足，無法檢查 Compute Engine、Cloud Storage 與 Pub/Sub，這三項需要有權限的帳號或到主控台確認。" — knowledge/raw/gcp-free-tier-audit-2026-11-25.md

## 執行前護欄

> "若任務涉及無免費額度的付費服務（Cloud SQL、GKE、Cloud NAT、Load Balancer、Vertex AI 付費端點），或規格超出上表，先暫停並告知費用，取得同意再執行。" — knowledge/raw/gcp-free-tier-spec.md
