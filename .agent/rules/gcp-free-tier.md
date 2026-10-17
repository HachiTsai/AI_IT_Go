# GCP 永久免費額度（Always Free Tier）作業規範

在執行任何 Google Cloud Platform (GCP) 相關操作（包含 `gcloud` CLI、Python SDK、Terraform 或部署腳本）時，**必須嚴格遵守 GCP Always Free 永久免費額度限制**，防止產生非預期費用。

## 1. 強制預設區域（Allowed Regions）

- **唯一首選預設區域**：**`us-central1`**（愛荷華）
- **次選免費額度區域**：`us-east1`（南卡羅來納）、`us-west1`（奧勒岡）
- **嚴格禁止**：
  - 未經使用者明確指示，**不得**將任何運算、儲存或無伺服器資源部署至 `asia-east1`、`asia-northeast1` 等非免費額度區域。
  - 所有服務應集中於同一區域（統一為 `us-central1`），避免跨區域資料傳輸（Cross-region Egress）產生網路費用。

## 2. 各項服務免費規格上限與強制參數

### Cloud Functions (Gen 2) / Cloud Run
- **區域**：必須指定 `--region=us-central1`。
- **實例上限**：必須設定 `--max-instances=1`（或極小上限），防止流量突波或迴圈觸發導致無上限擴展。
- **記憶體與 CPU**：預設使用輕量規格（如 `--memory=256Mi`）。
- **重試策略**：事件觸發（如 Pub/Sub）預設不啟用無限重試，避免程式例外時耗盡每月 200 萬次免費呼叫額度。

### Compute Engine (VM)
- **機型**：僅限 **`e2-micro`**（每月 1 台免費）。
- **區域**：僅限 `us-central1`、`us-west1`、`us-east1`。
- **磁碟類型與容量**：
  - 必須顯式指定 `--boot-disk-type=pd-standard`（標準永久磁碟），且總容量 **`<= 30 GB`**。
  - **注意**：GCP 預設的 `pd-balanced` 或 `pd-ssd` **不在**免費額度內，一旦建立會立即計費。

### Cloud Storage (GCS)
- **區域**：僅限 `us-central1`、`us-east1`、`us-west1` 的單一區域（Regional）Bucket，且選擇 `STANDARD` 儲存類別（合計 `<= 5 GB` 免費）。
- **禁止**使用 Multi-region（如 `US`、`ASIA`），以避免跨區複寫與讀取費用。

### Artifact Registry & Cloud Build
- **免費容量上限**：Artifact Registry 總儲存空間上限為 **`500 MB` (0.5 GB)**。
- 部署容器或 Cloud Functions 後，若產生過多舊版映像檔（Container Images）或非免費區域的暫存 Bucket（如 `gcf-v2-sources-*`），應主動清理。

### Secret Manager & Pub/Sub
- **Secret Manager**：保持全專案有效（Active）密鑰版本總數 **`<= 6 個`**（每月前 6 個版本免費；更新密鑰時應銷毀舊版本）。
- **Pub/Sub**：每月前 10 GB 訊息量免費，避免發送大型二進位 Payload。

## 3. Agent 安全護欄（執行前攔截）

- 若任務需求涉及**無免費額度之付費服務**（如 Cloud SQL、GKE 叢集、Cloud NAT、Load Balancer、Vertex AI 付費端點），或規格超出上述免費上限，Agent **必須在執行指令前暫停並明確告知使用者潛在費用**，取得使用者同意後才可執行。
