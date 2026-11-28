"""note.py add 的結束碼：Drive 上傳失敗必須讓呼叫端知道。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，不會連到 Google Drive。
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def _run_add(tmp_path, upload_line):
    fake = tmp_path / "gdrive"
    fake.write_text(
        "#!/bin/sh\n"
        'case "$1 $2" in\n'
        '  "readonly ls") echo "[]" ;;\n'
        '  "mutate mkdir") echo \'{"id": "FOLDER"}\' ;;\n'
        f'  "mutate upload") {upload_line} ;;\n'
        "esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = {"GDRIVE_BIN": str(fake), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), "add", "-c", "Test", "-t", "exit_code",
         "--content", "# body", "--repo", "R"],
        capture_output=True, text=True, env=env,
    )


def test_add_exits_nonzero_when_upload_fails(tmp_path):
    res = _run_add(tmp_path, 'echo "quota exceeded" >&2; exit 1')

    assert res.returncode == 1
    assert "上傳 Google Drive 失敗：quota exceeded" in res.stderr
    assert res.stdout == ""
    # 內容沒有存到雲端，必須告訴使用者本機暫存檔在哪裡
    assert "exit_code.md" in res.stderr


def test_add_exits_zero_when_upload_succeeds(tmp_path):
    res = _run_add(tmp_path, 'echo \'{"id": "FILE"}\'')

    assert res.returncode == 0, res.stderr
    assert "成功建立" in res.stdout
