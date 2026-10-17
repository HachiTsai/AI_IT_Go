# AI_IT_Go 開發與環境規範

## 1. 執行環境

- **雲端環境（Claude Web）**：
  - 進入專案目錄時會透過 `~/.bashrc` 自動觸發 `scripts/init.sh`，建立 `.venv`（Python 3.14）並啟用。
  - 若 `.venv` 尚未建立，請執行 `bash scripts/init.sh`。
- **本機環境（macOS）**：
  - 使用 Conda 環境 `ai-it-go`（`/opt/homebrew/Caskroom/miniforge/base/envs/ai-it-go/bin/python`，Python 3.14）。

## 2. 套件與依賴管理（重要規則）

- **禁止只安裝不記錄**：新增任何第三方套件時，**嚴禁**只執行 `pip install <pkg>` 或 `uv pip install <pkg>` 而未寫入依賴設定檔。
- **標準新增套件流程**：
  1. 優先使用 `uv add <pkg>`（自動寫入 `pyproject.toml`），並同步更新 `requirements.txt`（固定版本號 `==x.y.z`）。
  2. 若環境無 `uv`，安裝後必須立即查詢實際安裝版本（`python -m pip show <pkg>`），並同步將 `<pkg>==<version>` 寫入 `pyproject.toml` 與 `requirements.txt`。
- `committer.py` 在提交前會自動檢查 staged `.py` 檔案所匯入的第三方套件是否已記錄，以及 `pyproject.toml` 與 `requirements.txt` 是否同步。

## 3. Git 提交流程

所有提交一律遵循 [`.claude/skills/commit-workflow/SKILL.md`](.claude/skills/commit-workflow/SKILL.md)：

```bash
# 1. 暫存變更、檢查敏感檔與未記錄套件、輸出 diff 與模板
python .claude/skills/commit-workflow/scripts/committer.py

# 2. 將草擬好的訊息寫入 .git/COMMIT_MSG_TEMP 後提交並推送
python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage

# 小型變更快速提交
python .claude/skills/commit-workflow/scripts/committer.py --auto-quick
```

## 4. 雲端環境設定（Claude 網頁版萬用 Setup Script）

Claude 網頁版的「環境設定（Setup Script）」欄位只需貼上以下通用片段（不依賴啟動當下是否已 clone 專案，跨專案、跨語言皆可複用）：

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
