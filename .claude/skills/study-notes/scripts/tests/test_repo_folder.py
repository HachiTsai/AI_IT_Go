"""repo 子資料夾：拿不到資料夾 ID 時不得改傳根目錄。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，不會連到 Google Drive。
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
ADD = ["add", "-c", "Test", "-t", "repo_folder", "--content", "# body", "--repo", "R"]


def _run(tmp_path, mkdir_line, cli_args, ls_line='echo "[]"'):
    log = tmp_path / "calls.log"
    fake = tmp_path / "gdrive"
    fake.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{log}"\n'
        'case "$1 $2" in\n'
        f'  "readonly ls") {ls_line} ;;\n'
        f'  "mutate mkdir") {mkdir_line} ;;\n'
        '  "mutate upload") echo \'{"id": "FILE"}\' ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = {"GDRIVE_BIN": str(fake), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    res = subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), *cli_args], capture_output=True, text=True, env=env
    )
    return res, log.read_text(encoding="utf-8").splitlines()


def _upload_parent(calls):
    upload = next(c for c in calls if c.startswith("mutate upload")).split()
    return upload[upload.index("--parent") + 1]


@pytest.mark.parametrize(
    "mkdir_line",
    [
        'echo "Created folder: R (ID: NEWFOLDER)"',  # gdrive 執行檔內的文字輸出格式
        'echo \'{"id": "NEWFOLDER"}\'',
    ],
    ids=["text", "json"],
)
def test_add_uploads_into_newly_created_folder(tmp_path, mkdir_line):
    res, calls = _run(tmp_path, mkdir_line, ADD)

    assert res.returncode == 0, res.stderr
    assert _upload_parent(calls) == "NEWFOLDER"


@pytest.mark.parametrize(
    "mkdir_line",
    ['echo "permission denied" >&2; exit 1', 'echo "something unexpected"'],
    ids=["command-fails", "no-id-in-output"],
)
def test_add_aborts_without_upload_when_folder_id_unavailable(tmp_path, mkdir_line):
    res, calls = _run(tmp_path, mkdir_line, ADD)

    assert res.returncode == 1
    assert "無法取得 Drive 資料夾「R」" in res.stderr
    assert not [c for c in calls if c.startswith("mutate upload")]
    assert res.stdout == ""


def test_list_repo_reports_folder_error_without_traceback(tmp_path):
    res, _ = _run(tmp_path, 'echo "permission denied" >&2; exit 1', ["list", "--repo", "R"])

    assert res.returncode == 1
    assert "permission denied" in res.stderr
    assert "Traceback" not in res.stderr


@pytest.mark.parametrize(
    "ls_line",
    [
        'echo "rate limit exceeded" >&2; exit 1',
        'echo "something unexpected"',
        'echo \'{"error": "x"}\'',
    ],
    ids=["command-fails", "not-json", "not-a-list"],
)
def test_add_does_not_create_folder_when_listing_fails(tmp_path, ls_line):
    res, calls = _run(tmp_path, 'echo "Created folder: R (ID: DUPLICATE)"', ADD, ls_line=ls_line)

    assert res.returncode == 1
    assert "無法取得 Drive 資料夾「R」" in res.stderr
    assert "Traceback" not in res.stderr
    assert not [c for c in calls if c.startswith(("mutate mkdir", "mutate upload"))]


def test_add_reuses_existing_folder(tmp_path):
    listing = '''echo '[{"id": "EXISTING", "name": "R", "mimeType": "application/vnd.google-apps.folder"}]\''''
    res, calls = _run(tmp_path, "exit 1", ADD, ls_line=listing)

    assert res.returncode == 0, res.stderr
    assert _upload_parent(calls) == "EXISTING"
    assert not [c for c in calls if c.startswith("mutate mkdir")]


def test_add_creates_folder_when_listing_output_is_empty(tmp_path):
    res, calls = _run(tmp_path, 'echo "Created folder: R (ID: NEWFOLDER)"', ADD, ls_line=":")

    assert res.returncode == 0, res.stderr
    assert _upload_parent(calls) == "NEWFOLDER"
