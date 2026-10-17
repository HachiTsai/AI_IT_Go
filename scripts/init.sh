#!/bin/bash
# 專案環境初始化腳本（由 ~/.bashrc 延遲觸發，或手動執行 bash scripts/init.sh）
# 不使用 set -e：GCP 認證與 Python 環境各自獨立，一邊失敗不應中止另一邊。

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1) GCP 服務帳號認證（若環境變數設有 GCP_SA_KEY）
authenticate_gcp() {
  unset CLOUDSDK_AUTH_ACCESS_TOKEN
  if [ -n "$GCP_SA_KEY" ] && command -v gcloud >/dev/null 2>&1; then
    if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q hachi-gcp; then
      (
        umask 077
        key="$(mktemp)"
        trap 'rm -f "$key"' EXIT
        printf '%s' "$GCP_SA_KEY" > "$key"
        gcloud auth activate-service-account --key-file="$key" --quiet >/dev/null 2>&1
        gcloud config set project hachi-gcp --quiet >/dev/null 2>&1
      )
    fi
  fi
}

authenticate_gcp

# 2) Python 虛擬環境（雲端環境具備 uv 且未使用 Conda 時自動建立 .venv）
cd "$REPO_ROOT" || exit 1
if command -v uv >/dev/null 2>&1 && [ -z "$CONDA_DEFAULT_ENV" ]; then
  uv venv --allow-existing --python 3.14 .venv
  if [ -f "pyproject.toml" ]; then
    uv pip install --python .venv/bin/python -r pyproject.toml
  elif [ -f "requirements.txt" ]; then
    uv pip install --python .venv/bin/python -r requirements.txt
  fi
fi
