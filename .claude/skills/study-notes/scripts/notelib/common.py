"""共用工具：不依賴任何雲端後端。"""

import datetime
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import List, Optional

from .base import NoOpenError

DEFAULT_FOLDER_ID = "1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn"
# 無 gdrive CLI 且未設定 AGENT_STUDY_NOTES_DIR 時的本機暫存位置（不會同步到 Google Drive）
FALLBACK_CACHE_DIR = Path.home() / ".cache" / "agent_study_notes"


def get_current_repo_name() -> str:
    """自動偵測當前 Git Repository 名稱，若不在 git 內則回傳 'Common'"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).name
    except Exception:
        pass
    return "Common"


def sanitize_filename(name: str) -> str:
    """清理檔名中的非法字元"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name


def note_stem(category: str, title: str) -> str:
    """筆記檔名主體：<類別>_<標題>，標題已含類別前綴時不重複加。"""
    clean_cat = sanitize_filename(category)
    clean_raw_title = sanitize_filename(title)
    if clean_raw_title.startswith(f"{clean_cat}_"):
        return clean_raw_title
    return f"{clean_cat}_{clean_raw_title}"


def format_note(repo: str, category: str, title: str, content: str, tags: List[str]) -> str:
    """產生含 YAML frontmatter 的完整筆記文字。"""
    today = datetime.date.today().isoformat()
    tags_str = ", ".join(f'"{t.strip()}"' for t in tags if t.strip())
    frontmatter = (
        f"---\n"
        f'title: "{title}"\n'
        f'repo: "{repo}"\n'
        f'category: "{category}"\n'
        f"date: {today}\n"
        f"tags: [{tags_str}]\n"
        f"---\n\n"
    )
    return frontmatter + content.strip() + "\n"


def find_gdrive_bin() -> Optional[str]:
    """尋找 gdrive CLI 執行檔路徑"""
    env_bin = os.environ.get("GDRIVE_BIN")
    if env_bin and os.access(env_bin, os.X_OK):
        return env_bin
    custom_bin = Path.home() / ".gemini" / "antigravity" / "bin" / "gdrive"
    if custom_bin.exists() and os.access(custom_bin, os.X_OK):
        return str(custom_bin)
    system_bin = shutil.which("gdrive")
    if system_bin:
        return system_bin
    return None


def is_no_open(name: Optional[str]) -> bool:
    """資料夾名稱是否標記 no open：全形視同半形、不分大小寫，忽略所有標點、符號、空白與底線後含 noopen。

    寧可多擋：例如 `piano open` 也會符合，改資料夾名稱即可。
    """
    folded = unicodedata.normalize("NFKC", name or "").casefold()
    return "noopen" in re.sub(r"[\W_]+", "", folded)


def ensure_folder_allowed(name: Optional[str]) -> None:
    """no open 資料夾一律不進入（.claude/rules/project-workflow.md）。"""
    if is_no_open(name):
        raise NoOpenError(f"資料夾「{name}」標記為 no open，不進入")
