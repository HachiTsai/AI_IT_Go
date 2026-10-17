# Slack & GCP & GitHub 環境與監控完整配置指南

> **建立日期**：2026-10-17  
> **最後更新**：2026-10-17 17:32（完成 `.claude/` 單一真實來源架構與 `.agent/rules/AGENT.md` 轉接整合）  
> **專案儲存庫**：[`https://github.com/HachiTsai/AI_IT_Go.git`](https://github.com/HachiTsai/AI_IT_Go.git)  
> **GCP 專案**：`gen-lang-client-0215358824`（Google-AI-Studio）  
> **帳單帳戶**：`01F547-EAD5DC-D3D0C8`

---

## 1. GitHub 專案、規則庫與 Python 依賴管理

### 1.1 儲存庫與跨 Agent 單一真實來源架構（`.claude/` + `.agent/rules/AGENT.md`）
- **本機路徑**：`/Users/hachi/Git/AI_IT_Go`
- **主要分支**：`main`
- **設計核心（Single Source of Truth）**：
  為避免同時維護 `.claude/` 與 `.agent/` 兩套重複檔案或複雜的雙向 Symlink，全專案所有實體規則與技能統一以 **Claude 官方原生語法**集中於 **`.claude/`** 目錄下管理；Antigravity 則僅透過單一入口檔 `.agent/rules/AGENT.md` 的 `@[...]` 語法自動展開載入：

```text
├── CLAUDE.md                             # Claude 官方規則入口索引
├── pyproject.toml                        # Python 3.14 唯一套件依賴與工具設定來源（已廢除 requirements.txt）
├── .claude/                              # ⭐ 唯一真實來源（100% Claude 官方原生結構）
│   ├── rules/                            # 模組化規則庫（每條規則獨立管理）
│   │   ├── gcp-free-tier.md              # GCP Always Free 永久免費額度與區域（us-central1 等）硬性規範
│   │   ├── system-cli-tools.md           # 本機（Homebrew/Conda）與雲端系統層級 CLI 工具盤點與安裝規範
│   │   ├── python-environment.md         # Python 環境規範，內嵌完整 pyproject.toml 並保持 100% 雙向同步
│   │   └── git-commit-workflow.md        # 結構化 Git 提交流程與禁止事項規範
│   └── skills/
│       └── commit-workflow/              # 自動化提交流程 Skill（含 committer.py 與單元測試）
└── .agent/                               # Antigravity 輕量轉接層
    └── rules/
        └── AGENT.md                      # Antigravity 唯一導引入口，指向 .claude/ 並強制先測試後提交
```

### 1.2 本機環境配置（Conda `ai-it-go` 與系統 CLI 工具）
- **Python 虛擬環境**：
  - 版本：Python 3.14.8（Conda 環境名稱：`ai-it-go`）
  - 路徑：`/opt/homebrew/Caskroom/miniforge/base/envs/ai-it-go`
  - IDE 綁定：`.vscode/settings.json` 預設指向該直譯器。
- **系統層級 CLI 工具（詳見 `.claude/rules/system-cli-tools.md`）**：
  - 雲端與容器：`gcloud` (`589.0.0`，含 `alpha`/`beta` 組件)、`docker` (`28.3.3`)、`kubectl`、`minikube`
  - 版控與協作：`git` (`2.54.0`)、`gh` (`2.101.0`)、`lab`
  - 語言與套件：`conda` (`26.1.1`)、`uv` (`0.13.1`，已透過 Homebrew 補齊於 `/opt/homebrew/bin/uv`)、`pipx`、`node` (`v25.9.0`)
  - 搜尋與系統：`rg` (`15.2.0`)、`fd` (`10.5.0`)、`gpg` (`2.5.18`)、`sqlite3`、`mkdocs`

### 1.3 提交與同步防呆機制 (`commit-workflow`)
- 位於 `.claude/skills/commit-workflow/scripts/committer.py`。
- **提交前四大自動防護**：
  1. **測試先行鐵律**：於 `CLAUDE.md` 與 `.agent/rules/AGENT.md` 明訂任何變更必須先通過 `pytest` 與 `ruff check .` 驗證無誤才可 Commit。
  2. **敏感檔案攔截 (`find_sensitive`)**：禁止提交 `.env`、`credentials/`、`*.key`、`*.pem`。
  3. **Python 依賴漂移攔截 (`find_dependency_issues`)**：自動以 AST 掃描 staged `.py` 檔案匯入的第三方套件，比對 `pyproject.toml`，若有未記錄的套件會在提交時攔截並提示版本號。
  4. **跨檔案與雙端規則同步檢查 (`find_rule_sync_issues`)**：
     - 自動驗證根目錄 `pyproject.toml` 與 `.claude/rules/python-environment.md` 內嵌的 ` ```toml ` 區塊是否 100% 一致（讓 `python-environment.md` 可單獨攜帶至未來任何新專案直接還原 `pyproject.toml`）。
     - 自動確保 `.agent/rules/` 僅保留單一 `AGENT.md` 入口，且 `.claude/rules/*.md` 下所有規則皆已同步索引於 `CLAUDE.md` 與 `.agent/rules/AGENT.md`。
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

---

## 6. 2026-10-17 任務執行與架構演進紀錄

以下記錄本次 Session 完成的一連串環境建置、監控整合與規則架構重構歷程：

1. **GitHub 儲存庫初始化與本機 Conda 環境建置**
   - Clone `HachiTsai/AI_IT_Go` 至 `/Users/hachi/Git/AI_IT_Go`。
   - 建立本機 Conda 環境 `ai-it-go`（Python 3.14.8），安裝核心套件並綁定 `.vscode/settings.json`。
   - 移除 GitHub Repo 舊有的 Slack/Assistant 通知設定並驗證 Push 不再誤發舊通知。
2. **GCP OAuth 2.0 認證與 Slack 雙重即時監控部署**
   - 本機透過 Homebrew Cask 安裝 `gcloud-cli` (`589.0.0`) 與 `alpha`/`beta` 組件，改用 OAuth 2.0 ADC 授權並切換至 `Google-AI-Studio` (`gen-lang-client-0215358824`)，安全移除舊有 JSON 私鑰檔。
   - 建立 Cloud Monitoring Alerting Policy 監控 Gemini API `429 Rate Limit`，串接 GCP 原生 Slack Channel 推播至 `#gcp_google-ai-studio`。
   - 建立 `billing-alerts` Pub/Sub 主題與 Gen2 Cloud Function `billing-to-slack`（部署於 Always Free 免費區域 `us-central1`），綁定每月預算門檻（50%、90%、100%）自動推播彩色告警卡片至 Slack Webhook。
3. **廢除 `requirements.txt` 並實作 `pyproject.toml` 單一依賴內嵌同步**
   - 移除 `requirements.txt`，統一由 `pyproject.toml` 作為唯一 Python 依賴與工具設定來源。
   - 將完整的 `pyproject.toml` 內嵌於 `python-environment.md` 規則檔中，使單一規則檔具備跨專案完整移植能力，並於 `committer.py` 實作雙向自動比對。
4. **系統層級 CLI 工具盤點與獨立規範**
   - 盤點本機 Homebrew / Conda 系統工具，補齊安裝 `uv` (`0.13.1`)，並建立獨立的 `system-cli-tools.md` 規則檔，將作業系統 CLI 工具與 Python 套件依賴清楚解耦。
5. **收斂至 `.claude/` 單一真實來源與 `.agent/rules/AGENT.md` 轉接架構**
   - 移除 `.git/hooks/pre-commit` 與交叉 Symlink，將所有模組化規則（`gcp-free-tier.md`、`system-cli-tools.md`、`python-environment.md`、`git-commit-workflow.md`）與技能統一收斂於 `.claude/` 下，全面採用 Claude 官方原生語法。
   - 建立 `.agent/rules/AGENT.md` 作為 Antigravity 唯一導引入口，透過 `@[...]` 自動展開載入 `.claude/` 內所有規則與技能，並明訂「先通過 `pytest` 與 `ruff` 測試才可 Commit」之鐵律。
   - 擴充 `committer.py`（`find_rule_sync_issues`）與單元測試 `test_committer.py`（共 14 項測試全數通過），自動防範 `.agent/rules/` 混入重複檔案或漏更新 `CLAUDE.md`／`AGENT.md` 索引。

