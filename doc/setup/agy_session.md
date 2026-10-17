# Slack & GCP & GitHub 環境與監控完整配置指南

> **建立日期**：2026-10-17  
> **最後更新**：2026-10-17 16:18 (驗證 Webhook 移除測試)  
> **專案儲存庫**：[`https://github.com/HachiTsai/AI_IT_Go.git`](https://github.com/HachiTsai/AI_IT_Go.git)  
> **GCP 專案**：`gen-lang-client-0215358824`（Google-AI-Studio）  
> **帳單帳戶**：`01F547-EAD5DC-D3D0C8`

---

## 1. GitHub 專案與 Python 依賴管理

### 1.1 儲存庫結構
- **本機路徑**：`/Users/hachi/Git/AI_IT_Go`
- **主要分支**：`main`
- **核心設定檔**：
  - `pyproject.toml`：採用 PEP 621 標準規範 Python 3.14+ 依賴，支援 `uv add <套件>` 安裝自動記錄。
  - `requirements.txt`：固定 14 個核心依賴版本號（`==x.y.z`）。
  - `CLAUDE.md`：定義 Claude Web 與本機開發規範、依賴同步鐵律與 Setup Script 片段。
  - `.vscode/settings.json`：IDE 直譯器預設綁定本機 Conda 環境 `ai-it-go`。

### 1.2 本機 Conda 環境 (`ai-it-go`)
- **Python 版本**：Python 3.14.8
- **環境路徑**：`/opt/homebrew/Caskroom/miniforge/base/envs/ai-it-go`
- **啟用指令**：
  ```bash
  conda activate ai-it-go
  ```

### 1.3 提交與依賴檢查機制 (`commit-workflow`)
- 位於 `.claude/skills/commit-workflow/scripts/committer.py`。
- **提交前安全防護**：
  1. **敏感檔案檢查**：禁止提交 `.env`、`credentials/`、`*.key`、`*.pem`。
  2. **依賴漂移檢查 (`find_dependency_issues`)**：自動以 AST 掃描 staged `.py` 檔案匯入的第三方套件，比對 `pyproject.toml` 與 `requirements.txt`，若有未記錄的套件（如隨手 `pip install` 但漏寫檔案）會在提交時攔截並提示版本。
  3. **依賴雙向同步檢查**：檢查 `pyproject.toml` 與 `requirements.txt` 兩邊清單是否完全一致。
- **常用提交流程**：
  ```bash
  # 暫存變更並執行各項檢查、印出 diff 與草擬模板
  python .claude/skills/commit-workflow/scripts/committer.py

  # 提交已草擬好的訊息並自動推送（支援失敗指數退避重試）
  python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage
  ```

---

## 2. 雲端環境（Claude Web）與本機雙軌架構

### 2.1 痛點解析
- **Claude 網頁版**：每次啟動為全新無頭 Linux 容器，啟動執行 Setup Script 時專案 Repo 尚未 clone 完成，且關閉對話即清空環境。
- **Mac 本機**：持久化環境，適合使用使用者級 OAuth 授權，不需在硬碟放置私鑰檔。

### 2.2 雲端環境完整 Setup Script（供直接貼入 Claude 網頁版「環境設定」）
包含自動安裝 `uv`、自動安裝 Google Cloud SDK 與 `beta/alpha` 組件、切換為 `Google-AI-Studio` 專案，並安裝 Python 3.14 核心與 GCP 監控套件：

```bash
#!/bin/bash

# 1) 自動安裝 uv（若容器未內建）
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2) 自動安裝 Google Cloud CLI（若容器未內建）
if ! command -v gcloud >/dev/null 2>&1; then
  curl -fsSL https://sdk.cloud.google.com | bash --install-dir="$HOME" --disable-prompts >/dev/null 2>&1
  echo 'source "$HOME/google-cloud-sdk/path.bash.inc"' >> ~/.bashrc
  source "$HOME/google-cloud-sdk/path.bash.inc" 2>/dev/null || true
fi

# 3) GCP 認證：寫進 ~/.bashrc，切換為 Google-AI-Studio
cat >> ~/.bashrc <<'EOF'
unset CLOUDSDK_AUTH_ACCESS_TOKEN
[ -f "$HOME/google-cloud-sdk/path.bash.inc" ] && source "$HOME/google-cloud-sdk/path.bash.inc"

if [ -n "$GCP_SA_KEY" ] && command -v gcloud >/dev/null 2>&1; then
  if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q "@"; then
    umask 077; printf '%s' "$GCP_SA_KEY" > /tmp/sa.json
    gcloud auth activate-service-account --key-file=/tmp/sa.json --quiet >/dev/null 2>&1
    # 切換為 Google-AI-Studio 專案
    gcloud config set project gen-lang-client-0215358824 --quiet >/dev/null 2>&1
    rm -f /tmp/sa.json
  fi
fi
EOF

# 4) 安裝 gcloud beta/alpha 組件（監控與預算功能需要）
if command -v gcloud >/dev/null 2>&1; then
  gcloud components install beta alpha --quiet >/dev/null 2>&1 || true
fi

# 5) Python 3.14 虛擬環境與套件安裝
uv venv --allow-existing --python 3.14 ~/.venv || true
uv pip install --python ~/.venv/bin/python \
  pytest==9.1.1 requests==2.34.2 httpx==0.28.1 pydantic==2.14.1 \
  python-dotenv==1.2.4 pyyaml==6.0.3 rich==15.0.0 typer==0.27.3 \
  anthropic==1.13.0 mcp==2.3.0 tenacity==9.2.1 numpy==2.5.4 \
  pandas==3.0.6 ruff==0.17.0 pyright==1.1.414 \
  functions-framework google-cloud-pubsub google-cloud-monitoring || true

# 6) 自動啟用環境
echo '[ -f ~/.venv/bin/activate ] && source ~/.venv/bin/activate' >> ~/.bashrc

exit 0
```

### 2.3 專案初始化腳本 (`scripts/init.sh`) 與延遲觸發
- **GCP 服務帳號認證**：若環境變數存在 `GCP_SA_KEY`，使用 `umask 077` 與 `mktemp` 安全認證 `Google-AI-Studio`，並在結束時以 `trap` 立即刪除暫存私鑰檔。
- **Python 虛擬環境**：若系統具備 `uv` 且未啟用 Conda，自動建置 Python 3.14 `.venv` 並優先自 `pyproject.toml` 安裝依賴。
- **延遲觸發（Lazy Init）機制**：
  若希望 Setup Script 完全不寫死套件名稱，而是在進入專案目錄時自動觸發專案內的 `scripts/init.sh`，可採用以下寫入 `.bashrc` 的極簡模式：
  ```bash
  cat >> ~/.bashrc <<'BASHRC'
  if [ -f "./scripts/init.sh" ]; then
    _stamp="/tmp/.init_done_$(printf '%s' "$PWD" | tr '/' '_')"
    if [ ! -f "$_stamp" ]; then
      touch "$_stamp"
      bash ./scripts/init.sh
    fi
  fi
  if [ -f "./.venv/bin/activate" ] && [ "$VIRTUAL_ENV" != "$PWD/.venv" ]; then
    source "./.venv/bin/activate"
  fi
  BASHRC
  [ -f "./scripts/init.sh" ] && source ~/.bashrc || true
  ```

---

## 3. GCP 認證與專案切換

### 3.1 本機 GCP OAuth 2.0 (ADC) 授權
本機全面改用 Google 官方推薦的 OAuth 2.0 (Application Default Credentials)，免保管 `.json` 私鑰檔：
```bash
# 1. 透過瀏覽器授權 gcloud CLI 與 Python ADC
gcloud auth login --update-adc

# 2. 切換預設專案至 Google-AI-Studio
gcloud config set project gen-lang-client-0215358824

# 3. 綁定 ADC 配額計算專案（消除 Quota Project 警告）
gcloud auth application-default set-quota-project gen-lang-client-0215358824
```
- 認證金鑰保存位置：`~/.config/gcloud/application_default_credentials.json`
- 舊有的服務帳號私鑰（`boreal-doodad-470707-r8-156e7a0f6f77.json`）已安全移除。

---

## 4. Slack 雙重即時監控架構

目前針對 **Google-AI-Studio** 建置了兩套互補的監控機制：

```
[1] Gemini API 配額超限 (429) ──(即時)──> Cloud Monitoring ──> Slack 官方整合 ──> #gcp_google-ai-studio
[2] GCP 每月花費達 50%/90%/100% ───────> Cloud Billing ────> Pub/Sub 主題 ──> Cloud Function ──> Slack Webhook
```

### 4.1 即時配額超限告警 (Quota / 429 Rate Limit)
- **警報政策名稱**：`Gemini API 配額超限告警 (429 Rate Limit)`
- **政策 ID**：`projects/gen-lang-client-0215358824/alertPolicies/3882828072115366994`
- **監控服務**：`generativelanguage.googleapis.com` (Gemini API)
- **觸發條件**：`serviceruntime.googleapis.com/api/request_count` 出現 HTTP 回應碼 `429 Too Many Requests (Resource Exhausted)`
- **接收管道**：GCP 原生 Slack Notification Channel `spent` ➔ 頻道 `#gcp_google-ai-studio`（Workspace: `Hachi`）
- **特性**：**秒級即時告警**，附帶指標卡片與控制台連結。

### 4.2 計費預算自動推播服務 (Billing Budget to Slack)
因 GCP 帳單預算不支援直接連結 Slack，採用標準事件驅動無伺服器架構轉發：

1. **Pub/Sub 主題**：
   - 名稱：`projects/gen-lang-client-0215358824/topics/billing-alerts`
   - 綁定帳單預算：`每月預算`（預算 ID：`09e4620e-8e83-438f-9abe-a518701fa6c4`，金額 100 TWD，門檻 50%、90%、100%）。
2. **轉發 Cloud Function (`billing-to-slack`)**：
   - **部屬區域**：`us-central1`（位於 **GCP Always Free 永久免費額度** 區域，每月 200 萬次呼叫免費）。
   - **觸發來源**：`billing-alerts` Pub/Sub 主題。
   - **目標端點**：Slack Incoming Webhook。
   - **訊息格式**：自動解析預算百分比，帶有彩色告警邊條（綠色、黃色 50%、橙色 90%、紅色 100%）與詳細支出數字。

---

## 5. 驗證與日常維護指令速查

### 測試 Slack Webhook 連線
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🔔 測試訊息"}' \
  'https://hooks.slack.com/services/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'
```

### 模擬發送預算警報至 Pub/Sub
```bash
gcloud pubsub topics publish billing-alerts \
  --project=gen-lang-client-0215358824 \
  --message='{"budgetDisplayName":"每月預算測試","costAmount":90.0,"budgetAmount":100.0,"currencyCode":"TWD"}'
```

### 檢查 Cloud Function 執行日誌
```bash
gcloud functions logs read billing-to-slack \
  --gen2 \
  --region=us-central1 \
  --project=gen-lang-client-0215358824 \
  --limit=10
```

### 檢查本機專案測試與語法
```bash
cd /Users/hachi/Git/AI_IT_Go
conda activate ai-it-go
python -m pytest
ruff check .
```
