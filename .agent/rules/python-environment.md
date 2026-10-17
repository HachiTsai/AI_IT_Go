# Python 執行環境與套件依賴同步規範

## 1. 執行環境選擇

- **本機環境（macOS / Antigravity）**：
  - 統一使用 Conda 環境 `ai-it-go`（Python 3.14，路徑：`/opt/homebrew/Caskroom/miniforge/base/envs/ai-it-go/bin/python`）。
  - 執行任何 Python 腳本、`pytest`、`ruff` 或 `pyright` 時，優先指定該環境的直譯器與執行檔。
- **雲端環境（Claude Web）**：
  - 使用專案目錄下的 `.venv`（或家目錄 `~/.venv`），由 Setup Script 或 `scripts/init.sh` 自動以 `uv` 建立。

## 2. 套件安裝與依賴同步鐵律

- **嚴禁只安裝不記錄**：新增任何第三方套件時，**禁止**只執行 `pip install <pkg>` 或 `uv pip install <pkg>` 而不更新專案依賴設定檔。
- **標準新增套件步驟**：
  1. 安裝套件後，必須查詢實際安裝版本號（如 `python -m pip show <pkg>`）。
  2. **同步更新兩份依賴檔**：將 `<pkg>==<version>` 同時寫入 `pyproject.toml` 與 `requirements.txt` 對應分類中。
- 提交前 `committer.py` 會透過 AST 自動檢查所有 staged `.py` 檔案的 `import` 語句與兩份依賴檔的一致性。
