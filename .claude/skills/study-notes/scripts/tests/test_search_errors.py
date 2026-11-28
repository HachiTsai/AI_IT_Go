"""search：只搜尋筆記資料夾；Drive 查詢失敗不得顯示成「找不到筆記」。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，不會連到 Google Drive。
假的 `readonly search` 模擬全 Drive 搜尋，會回傳筆記資料夾以外的檔案。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
FOLDER = "application/vnd.google-apps.folder"
DOC = "application/vnd.google-apps.document"


def _item(file_id, name, mime=DOC):
    return {"id": file_id, "name": name, "mimeType": mime}


TREE = {
    "ROOT": [_item("SUB", "R", FOLDER), _item("OTHER", "S", FOLDER), _item("1", "Root_Keyword_note")],
    "SUB": [_item("2", "keyword_in_R"), _item("3", "unrelated"), _item("4", "keyword_photo", "image/png")],
    "OTHER": [_item("5", "keyword_in_S")],
}


def _ok(items):
    return f"echo '{json.dumps(items)}'"


def _search(tmp_path, args=("keyword",), **overrides):
    """overrides：以資料夾 ID 指定該次 ls 要執行的 shell 指令。"""
    log = tmp_path / "calls.log"
    cases = "".join(f"    {fid}) {overrides.get(fid, _ok(items))} ;;\n" for fid, items in TREE.items())
    fake = tmp_path / "gdrive"
    fake.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{log}"\n'
        'case "$1 $2" in\n'
        '  "readonly ls") case "$3" in\n' + cases + "  esac ;;\n"
        f'  "readonly search") {_ok([_item("X", "keyword_outside_notes")])} ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = {
        "GDRIVE_BIN": str(fake),
        "AGENT_STUDY_NOTES_FOLDER_ID": "ROOT",
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
    }
    res = subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), "search", *args], capture_output=True, text=True, env=env
    )
    calls = log.read_text(encoding="utf-8").splitlines()
    assert not [c for c in calls if c.startswith("mutate")], "search 是唯讀動作"
    return res


def test_search_only_returns_notes_under_notes_folder(tmp_path):
    res = _search(tmp_path)

    assert res.returncode == 0, res.stderr
    assert "3 筆" in res.stdout
    for name in ("Root_Keyword_note", "keyword_in_R", "keyword_in_S"):  # 比對不分大小寫
        assert name in res.stdout
    for name in ("keyword_outside_notes", "unrelated", "keyword_photo"):
        assert name not in res.stdout


def test_search_with_repo_stays_in_that_folder(tmp_path):
    res = _search(tmp_path, ("keyword", "--repo", "R"))

    assert res.returncode == 0, res.stderr
    assert "1 筆" in res.stdout
    assert "[R] keyword_in_R" in res.stdout


def test_search_unknown_repo_finds_nothing_and_creates_no_folder(tmp_path):
    res = _search(tmp_path, ("keyword", "--repo", "missing"))

    assert res.returncode == 0, res.stderr
    assert "未找到匹配關鍵字" in res.stdout


def test_search_says_not_found_only_when_query_succeeds(tmp_path):
    res = _search(tmp_path, ("nothing-matches",))

    assert res.returncode == 0, res.stderr
    assert "未找到匹配關鍵字" in res.stdout


@pytest.mark.parametrize(
    "folder_id, command",
    [
        ("ROOT", 'echo "rate limit exceeded" >&2; exit 1'),
        ("ROOT", 'echo "something unexpected"'),
        ("ROOT", 'echo \'{"error": "x"}\''),
        ("SUB", 'echo "rate limit exceeded" >&2; exit 1'),
    ],
    ids=["root-fails", "not-json", "not-a-list", "subfolder-fails"],
)
def test_search_reports_query_failure(tmp_path, folder_id, command):
    res = _search(tmp_path, **{folder_id: command})

    assert res.returncode == 1
    assert "查詢 Drive 清單失敗" in res.stderr
    assert "未找到" not in res.stdout
    assert "Traceback" not in res.stderr
