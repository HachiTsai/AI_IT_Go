"""list／read：Drive 查詢失敗不得顯示成「沒有筆記」或「找不到筆記」。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，不會連到 Google Drive。
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
FOLDERS = '''echo '[{"id": "SUB", "name": "R", "mimeType": "application/vnd.google-apps.folder"}]\''''
FAIL = 'echo "rate limit exceeded" >&2; exit 1'


def _run(tmp_path, cli_args, root_ls, sub_ls='echo "[]"', export="exit 1"):
    fake = tmp_path / "gdrive"
    fake.write_text(
        "#!/bin/sh\n"
        'case "$1 $2" in\n'
        '  "readonly ls")\n'
        '    if [ "$3" = "ROOT" ]; then\n'
        f"      {root_ls}\n"
        "    else\n"
        f"      {sub_ls}\n"
        "    fi ;;\n"
        f'  "readonly export") {export} ;;\n'
        '  "readonly download") exit 1 ;;\n'
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
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), *cli_args], capture_output=True, text=True, env=env
    )


@pytest.mark.parametrize(
    "root_ls, sub_ls, args",
    [
        (FAIL, 'echo "[]"', ["list"]),
        ('echo "something unexpected"', 'echo "[]"', ["list"]),
        (FOLDERS, FAIL, ["list"]),
        (FOLDERS, FAIL, ["list", "--repo", "R"]),
    ],
    ids=["root-fails", "root-not-json", "subfolder-fails", "repo-folder-fails"],
)
def test_list_reports_query_failure(tmp_path, root_ls, sub_ls, args):
    res = _run(tmp_path, args, root_ls, sub_ls)

    assert res.returncode == 1
    assert "查詢 Drive 清單失敗" in res.stderr
    assert "沒有筆記" not in res.stdout
    assert "Traceback" not in res.stderr


def test_list_says_no_notes_only_when_query_succeeds(tmp_path):
    res = _run(tmp_path, ["list"], FOLDERS)

    assert res.returncode == 0, res.stderr
    assert "沒有筆記" in res.stdout


def test_read_by_file_id_still_works_when_listing_fails(tmp_path):
    res = _run(tmp_path, ["read", "FILEID", "--repo", "R"], FAIL, export='echo "note body" > "$4"')

    assert res.returncode == 0, res.stderr
    assert "note body" in res.stdout


def test_read_reports_query_failure_instead_of_not_found(tmp_path):
    res = _run(tmp_path, ["read", "some_title"], FAIL)

    assert res.returncode == 1
    assert "查詢 Drive 清單失敗" in res.stderr
    assert "找不到筆記" not in res.stderr
