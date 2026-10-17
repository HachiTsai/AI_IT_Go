# 系統層級 CLI 工具盤點與安裝規範

本規則定義跨專案通用的系統層級 CLI 工具清單、執行檔路徑與標準安裝指令。當 Agent 在本機（macOS）或雲端（Claude Web / Linux 容器）執行任務時，應優先使用下列標準工具與路徑。

---

## 1. 核心系統 CLI 工具清單（macOS 本機標準環境）

| 類別 | 工具名稱 | 本機標準路徑 | 版本基準 | 用途與規範 |
| :--- | :--- | :--- | :--- | :--- |
| **雲端與容器** | `gcloud` | `/opt/homebrew/bin/gcloud` | `589.0.0+` | Google Cloud SDK（必裝 `alpha`、`beta` 組件） |
| | `docker` | `/opt/homebrew/bin/docker` | `28.3.3+` | 容器建置與管理 CLI |
| | `kubectl` | `/opt/homebrew/bin/kubectl` | 最新穩定版 | Kubernetes 叢集管理 |
| | `minikube` | `/opt/homebrew/bin/minikube` | 最新穩定版 | 本機 K8s 測試叢集 |
| **版控與協作** | `git` / `git-lfs` | `/usr/bin/git` | `2.54.0+` | 版本控制與大型檔案管理 |
| | `gh` | `/opt/homebrew/bin/gh` | `2.101.0+` | GitHub CLI（PR、Issue、Webhook、Repo 管理） |
| | `lab` | `/opt/homebrew/bin/lab` | 最新穩定版 | GitLab CLI |
| **語言與套件管理** | `conda` | `/opt/homebrew/Caskroom/miniforge/base/bin/conda` | `26.1.1+` | 本機 Python 虛擬環境管理（Miniforge） |
| | `uv` | `/opt/homebrew/bin/uv` | `0.13.1+` | 高速 Python 套件與虛擬環境管理（雲端與本機通用） |
| | `pipx` | `/opt/homebrew/bin/pipx` | 最新穩定版 | 全域隔離安裝 Python CLI 工具 |
| | `node` / `npm` | `/opt/homebrew/bin/node` | `v25.9.0+` | Node.js 執行環境與 MCP Server 依賴 |
| **高速搜尋與系統** | `rg` (ripgrep) | `/opt/homebrew/bin/rg` | `15.2.0+` | 程式碼全文檢索首選（取代傳統 `grep`） |
| | `fd` | `/opt/homebrew/bin/fd` | `10.5.0+` | 高速檔案查找首選（取代傳統 `find`） |
| | `gpg` | `/opt/homebrew/bin/gpg` | `2.5.18+` | GnuPG 金鑰與簽章管理 |
| | `sqlite3` | `/usr/bin/sqlite3` | `3.54.0+` | 輕量級資料庫檢視與查詢 |
| | `mkdocs` | `/opt/homebrew/bin/mkdocs` | 最新穩定版 | `mkdocs-material` 文件網站生成 |

---

## 2. 本機（macOS Homebrew）一鍵補齊指令

在新 Mac 環境或檢查發現缺少核心 CLI 工具時，統一透過 Homebrew 安裝：

```bash
# 核心 CLI 工具（Formulae）
brew install gh uv ripgrep fd pipx node kubernetes-cli minikube docker git-lfs gnupg mkdocs-material

# 雲端與環境管理（Casks）
brew install --cask gcloud-cli miniforge

# GCP CLI 進階組件（Cloud Monitoring / Billing Budgets 必備）
gcloud components install alpha beta --quiet
```

---

## 3. 雲端容器環境（Claude Web / Linux）自動安裝片段

在無頭 Linux 容器（如 Claude Web Setup Script）中，若未內建 `uv` 與 `gcloud`，標準安裝與認證片段如下：

```bash
# 1) 自動安裝 uv
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2) 自動安裝 Google Cloud SDK 與 alpha/beta 組件
if ! command -v gcloud >/dev/null 2>&1; then
  curl -fsSL https://sdk.cloud.google.com | bash --install-dir="$HOME" --disable-prompts >/dev/null 2>&1
  echo 'source "$HOME/google-cloud-sdk/path.bash.inc"' >> ~/.bashrc
  source "$HOME/google-cloud-sdk/path.bash.inc" 2>/dev/null || true
fi
if command -v gcloud >/dev/null 2>&1; then
  gcloud components install beta alpha --quiet >/dev/null 2>&1 || true
fi
```
