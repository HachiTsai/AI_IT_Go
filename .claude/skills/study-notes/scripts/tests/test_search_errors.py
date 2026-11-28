"""search：Drive 查詢失敗不得顯示成「找不到筆記」。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，不會連到 Google Drive。
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]


def _search(tmp_path, search_line):
    fake = tmp_path / "gdrive"
    fake.write_text(
        f'#!/bin/sh\ncase "$1 $2" in\n  "readonly search") {search_line} ;;\nesac\n', encoding="utf-8"
    )
    fake.chmod(0o755)
    env = {"GDRIVE_BIN": str(fake), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), "search", "keyword"], capture_output=True, text=True, env=env
    )


@pytest.mark.parametrize(
    "search_line",
    [
        'echo "rate limit exceeded" >&2; exit 1',
        'echo "something unexpected"',
        'echo \'{"error": "x"}\'',
    ],
    ids=["command-fails", "not-json", "not-a-list"],
)
def test_search_reports_query_failure(tmp_path, search_line):
    res = _search(tmp_path, search_line)

    assert res.returncode == 1
    assert "搜尋 Drive 失敗" in res.stderr
    assert "未找到" not in res.stdout
    assert "Traceback" not in res.stderr


def test_search_says_not_found_only_when_query_succeeds(tmp_path):
    res = _search(tmp_path, 'echo "[]"')  # 真實 gdrive 查無結果的輸出

    assert res.returncode == 0, res.stderr
    assert "未找到匹配關鍵字" in res.stdout


def test_search_lists_matches(tmp_path):
    hit = '''echo '[{"id": "FILE", "name": "keyword_note", "mimeType": "application/vnd.google-apps.document"}]\''''
    res = _search(tmp_path, hit)

    assert res.returncode == 0, res.stderr
    assert "keyword_note" in res.stdout
