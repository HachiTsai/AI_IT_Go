# GCP 永久免費額度規格整理

來源：專案規則 .claude/rules/gcp-free-tier.md。以下是本專案採用的作業上限，不是 Google 官方文件的原文；官方額度可能調整，正式使用前請對照官方頁面。

## 區域

- 首選：us-central1
- 次選：us-east1、us-west1
- 未經明確指示，不部署到 asia-east1、asia-northeast1 等區域
- 服務集中在同一區域，避免跨區網路費用

## 各服務規格上限

| 服務 | 必要設定與上限 |
| :--- | :--- |
| Cloud Functions Gen 2／Cloud Run | region=us-central1、max-instances=1、memory 256Mi、事件觸發不啟用無限重試（每月 200 萬次呼叫額度） |
| Compute Engine | 僅 e2-micro（每月 1 台）、僅 us-central1／us-west1／us-east1、boot disk 用 pd-standard 且 30 GB 以內；pd-balanced 與 pd-ssd 不在免費範圍 |
| Cloud Storage | 單一區域 Bucket、STANDARD 類別、合計 5 GB 以內；禁用 Multi-region |
| Artifact Registry／Cloud Build | 總儲存 500 MB 以內；定期清理舊映像與 gcf-v2-sources-* 暫存 Bucket |
| Secret Manager | 有效密鑰版本合計 6 個以內；更新時銷毀舊版 |
| Pub/Sub | 每月前 10 GB 免費；避免大型二進位 Payload |

## 執行前護欄

若任務涉及無免費額度的付費服務（Cloud SQL、GKE、Cloud NAT、Load Balancer、Vertex AI 付費端點），或規格超出上表，先暫停並告知費用，取得同意再執行。

## 維護方式

- 每次 GCP 操作前對照本表（對應 Jira HAC-12）。
- 定期核對官方免費額度頁面是否有變動。
