# Colab CLI 與 Colab MCP 連接評估（2026-11-25）

整理自專案記憶中 2026-11-12 的紀錄與 hachi 本機實測；本次未重新測試，也未在雲端容器測試。

## 兩種官方做法

- Colab CLI：2026-06-05 發表，Linux 與 macOS 可用，指令有 new、exec、run、stop、usage、drivemount、auth，預設以 ADC 認證。
- Colab MCP 伺服器：2026-03-17 發表，在本機以 uvx 執行，需要本機 MCP 用戶端與瀏覽器中開啟的 Colab 筆記本分頁。

## 實測結果（2026-11-12，hachi 的 Mac，CLI 0.8.0）

- 先執行 gcloud auth application-default login 並授權四個範圍後，new、exec、stop、usage 皆可用。
- 沒有 ADC 檔案時，new 會在建立 VM 之前失敗。
- 0.8.0 的說明顯示預設認證為 oauth2，但 README 寫 adc，所以要明確加上 --auth=adc。

## 風險與使用界線

- 加速器 VM 會持續消耗運算單元，直到執行 colab stop。
- colab exec 會把檔案內容送到遠端 VM；不要放入金鑰或私人資料。
- colab drivemount 會把 Drive 暴露給 VM，與「不得進入 private 資料夾」的規則衝突，只能掛載專用資料夾。
- ADC 使用 hachi 的個人 Google 帳號，不是專案的服務帳號。
- MCP 安裝要固定在標籤或 commit，不要直接用 git HEAD。

## 結論

- 可用，但只適合在 hachi 的本機環境執行；雲端容器沒有瀏覽器分頁與個人 ADC，不適用。
- 需要 GPU 或長時間運算時再用，其餘情況用本機或 Cloud Run 即可。
