# GCP 免費額度規格對照檢查（2026-11-25）

檢查方式：用專案服務帳號（唯讀角色）執行 gcloud 唯讀指令，對照 gcp-free-tier-spec.md。金鑰與帳號細節未寫入本檔。

## 可驗證的項目

| 項目 | 現況 | 是否符合規格 |
| :--- | :--- | :--- |
| Cloud Functions | 只有 billing-to-slack（Gen 2，us-central1，256M 記憶體，Pub/Sub 觸發且不重試） | 區域、記憶體、重試符合 |
| 實例上限 | maxInstanceCount 為 100 | 不符：規格要求 max-instances 為 1 |
| Artifact Registry | 只有 gcf-artifacts（us-central1，約 10 MB） | 符合：500 MB 以內 |
| Secret Manager | API 未啟用 | 符合：沒有密鑰版本 |

## 無法驗證的項目

服務帳號權限不足，無法檢查 Compute Engine、Cloud Storage 與 Pub/Sub，這三項需要有權限的帳號或到主控台確認。

## 備註

- billing／budget／Slack 通知已於 2026-11-18 停用，billing-to-slack 目前可能已不需要；是否把實例上限改為 1 或直接刪除，需 hachi 決定，本次未做任何變更。
