# Python 執行環境與 `pyproject.toml` 同步規範

## 1. 執行環境選擇

- **本機環境（macOS / Antigravity）**：
  - 統一使用 Conda 環境 `ai-it-go`（Python 3.14，路徑：`/opt/homebrew/Caskroom/miniforge/base/envs/ai-it-go/bin/python`）。
  - 執行任何 Python 腳本、`pytest`、`ruff` 或 `pyright` 時，優先指定該環境的直譯器與執行檔。
- **雲端環境（Claude Web）**：
  - 使用專案目錄下的 `.venv`（或家目錄 `~/.venv`），由 Setup Script 或 `scripts/init.sh` 自動以 `uv` 建立（`uv pip install --python .venv/bin/python -r pyproject.toml`）。

## 2. 單一依賴來源與雙向同步鐵律

- **廢除 `requirements.txt`**：專案統一以 **`pyproject.toml`** 作為唯一的套件依賴與工具設定來源，不再維護 `requirements.txt`。
- **禁止只安裝不記錄**：新增任何第三方套件時，**嚴禁**只執行 `pip install <pkg>` 或 `uv pip install <pkg>` 而不更新設定檔。
- **規則檔與設定檔必須完全一致**：
  - 下方第 3 節收錄了標準 `pyproject.toml` 完整內容，使本規則檔具備跨專案獨立移植能力（新專案只需帶上本規則檔即可直接生成 `pyproject.toml`）。
  - 當透過 `uv add <pkg>` 或手動在 `pyproject.toml` 新增／更新套件時，**必須同步更新本檔案（`.claude/rules/python-environment.md`）下方區塊**，確保兩者的依賴清單與版本號 100% 一致。
  - `committer.py` 在提交前會自動檢查 staged `.py` 的 `import` 套件是否已寫入 `pyproject.toml`，並比對 `pyproject.toml` 與本規則檔內的 `toml` 區塊是否一致。

## 3. 標準 `pyproject.toml` 內容（須與專案根目錄 `pyproject.toml` 保持一致）

```toml
[project]
name = "ai-it-go"
version = "0.1.0"
description = "AI IT 的修練場：實驗工具、驗證做法、累積可重複使用的技能（skills）與筆記"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    # 核心
    "pytest==9.1.1",
    "requests==2.34.2",
    "httpx==0.28.1",
    "pydantic==2.14.1",
    "python-dotenv==1.2.4",
    "pyyaml==6.0.3",
    "rich==15.0.0",
    "typer==0.27.3",
    # AI
    "anthropic==1.13.0",
    "mcp==2.3.0",
    "tenacity==9.2.1",
    "numpy==2.5.4",
    "pandas==3.0.6",
    # GCP / 雲端服務
    "functions-framework==3.10.2",
    # 品質工具
    "ruff==0.17.0",
    "pyright==1.1.414",
]

[tool.pytest.ini_options]
testpaths = [".claude/skills/commit-workflow/scripts/tests", "tests"]

[tool.ruff]
line-length = 120
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501", "E741"]
```
