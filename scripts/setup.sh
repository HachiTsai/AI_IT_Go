#!/bin/bash
# 雲端環境 Setup script：設定 GCP 認證與 Python 3.14 環境。
# 環境設定欄位只需填一行：bash /home/user/AI_IT_Go/scripts/setup.sh
# 不使用 set -e：GCP 與 Python 是兩件獨立的事，一邊失敗不應中止另一邊。

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1) GCP 認證：寫進 ~/.bashrc，每次開 shell 時才驗證。
#    GCP_SA_KEY 請放在環境的 secrets 設定，不要寫進此檔或 repo。
cat >> ~/.bashrc <<'BASHRC'
unset CLOUDSDK_AUTH_ACCESS_TOKEN
if [ -n "$GCP_SA_KEY" ] && ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q hachi-gcp; then
  (
    umask 077
    key="$(mktemp)"
    trap 'rm -f "$key"' EXIT
    printf '%s' "$GCP_SA_KEY" > "$key"
    gcloud auth activate-service-account --key-file="$key" --quiet >/dev/null 2>&1
    gcloud config set project hachi-gcp --quiet >/dev/null 2>&1
  )
fi
BASHRC

# 2) Python 3.14 虛擬環境
cd "$REPO_ROOT" || exit 1
uv venv --allow-existing --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements.txt
