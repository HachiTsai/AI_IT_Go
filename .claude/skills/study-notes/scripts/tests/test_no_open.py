"""名稱含「no open」的資料夾一律不進入（.claude/rules/project-workflow.md）。

以 GDRIVE_BIN 指向假的 gdrive 腳本跑完整 CLI，並檢查呼叫紀錄；不會連到 Google Drive。
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from notelib.common import is_no_open  # noqa: E402

FOLDER = "application/vnd.google-apps.folder"
DOC = "application/vnd.google-apps.document"


def _item(file_id, name, mime=DOC):
    return {"id": file_id, "name": name, "mimeType": mime}


LISTINGS = {
    "ROOT": [_item("SUB", "R", FOLDER), _item("LOCKED", "Finance (No_Open)", FOLDER)],
    "SUB": [_item("OK", "keyword_ok")],
    "LOCKED": [_item("SECRET", "keyword_secret")],
}
INFO = {
    "OK": {"name": "keyword_ok", "parents": ["SUB"]},
    "SUB": {"name": "R", "parents": ["ROOT"]},
    "ROOT": {"name": "notes", "parents": []},
    "SECRET": {"name": "keyword_secret", "parents": ["MID"]},
    "LINK": {"name": "link", "mimeType": "application/vnd.google-apps.shortcut", "parents": ["ROOT"]},
    "MID": {"name": "inner", "parents": ["LOCKED"]},
    "LOCKED": {"name": "Finance (No_Open)", "parents": ["ROOT"]},
}


def _run(tmp_path, *args):
    log = tmp_path / "calls.log"
    log.write_text("", encoding="utf-8")

    def cases(table):
        return "".join(f"    {k}) echo '{json.dumps(v)}' ;;\n" for k, v in table.items())

    fake = tmp_path / "gdrive"
    fake.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{log}"\n'
        'case "$1 $2" in\n'
        '  "readonly ls") case "$3" in\n' + cases(LISTINGS) + "  esac ;;\n"
        '  "readonly info") case "$3" in\n' + cases(INFO) + "    *) exit 1 ;;\n  esac ;;\n"
        '  "readonly export") echo "body of $3" > "$4" ;;\n'
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
    res = subprocess.run([sys.executable, str(SCRIPTS / "note.py"), *args], capture_output=True, text=True, env=env)
    return res, log.read_text(encoding="utf-8").splitlines()


def _entered_locked(calls):
    """對鎖定資料夾或其內檔案下過 info 以外的任何指令。"""
    return [c for c in calls if not c.startswith("readonly info") and {"LOCKED", "SECRET", "MID"} & set(c.split())]


@pytest.mark.parametrize("name", ["no open", "No Open", "NO_OPEN 私人", "財務 (no-open)", "noopen", "no.open", "no\u2013open", "no/open", "ｎｏ　ｏｐｅｎ"])
def test_is_no_open_matches_marked_names(name):
    assert is_no_open(name)


@pytest.mark.parametrize("name", ["AI_IT_Go", "open notes", "nothing to open", "", None])
def test_is_no_open_ignores_other_names(name):
    assert not is_no_open(name)


@pytest.mark.parametrize("args", [("list",), ("search", "keyword")], ids=["list", "search"])
def test_walking_all_folders_skips_marked_folder(tmp_path, args):
    res, calls = _run(tmp_path, *args)

    assert res.returncode == 0, res.stderr
    assert "keyword_ok" in res.stdout
    assert "keyword_secret" not in res.stdout
    assert not _entered_locked(calls)


@pytest.mark.parametrize(
    "args",
    [
        ("add", "-c", "T", "-t", "x", "--content", "body", "--repo", "Finance (No_Open)"),
        ("list", "--repo", "Finance (No_Open)"),
        ("search", "keyword", "--repo", "Finance (No_Open)"),
        ("read", "SECRET", "--repo", "Finance (No_Open)"),
    ],
    ids=["add", "list", "search", "read"],
)
def test_marked_repo_is_refused_before_any_drive_call(tmp_path, args):
    res, calls = _run(tmp_path, *args)

    assert res.returncode == 1
    assert "no open" in res.stderr
    assert "Traceback" not in res.stderr
    assert calls == []


def test_read_by_id_refuses_file_under_marked_ancestor(tmp_path):
    res, calls = _run(tmp_path, "read", "SECRET")

    assert res.returncode == 1
    assert "no open" in res.stderr
    assert "body of" not in res.stdout
    assert not _entered_locked(calls)


def test_read_by_id_refuses_when_ancestors_cannot_be_checked(tmp_path):
    res, calls = _run(tmp_path, "read", "UNKNOWN")

    assert res.returncode == 1
    assert "無法確認" in res.stderr
    assert not [c for c in calls if c.startswith(("readonly export", "readonly download"))]


@pytest.mark.parametrize("identifier", ["OK", "keyword_ok"], ids=["by-id", "by-name"])
def test_read_normal_note_still_works(tmp_path, identifier):
    res, _ = _run(tmp_path, "read", identifier)

    assert res.returncode == 0, res.stderr
    assert "body of OK" in res.stdout


def test_read_by_id_refuses_shortcut(tmp_path):
    # 捷徑本身的上層合法，但目標可能在 no open 資料夾內
    res, calls = _run(tmp_path, "read", "LINK")

    assert res.returncode == 1
    assert "捷徑" in res.stderr
    assert not [c for c in calls if c.startswith(("readonly export", "readonly download"))]


def test_listing_failure_is_reported_even_if_identifier_mentions_no_open(tmp_path, monkeypatch):
    # 呼叫者的字串含 no open，不能讓「無法確認」被當成 no open 拒絕
    monkeypatch.setitem(LISTINGS, "ROOT", {"error": "listing broken"})
    res, _ = _run(tmp_path, "read", "my no open title")

    assert res.returncode == 1
    assert "查詢 Drive 清單失敗" in res.stderr


# ---- 本機後端（AGENT_STUDY_NOTES_DIR 可能指向 Drive 同步目錄） ----

def _local(tmp_path):
    from notelib.local_backend import LocalStorageBackend

    root = tmp_path / "notes"
    for folder, name in (("R", "keyword_ok"), ("Finance no open", "keyword_secret")):
        (root / folder).mkdir(parents=True)
        (root / folder / f"{name}.md").write_text("keyword body", encoding="utf-8")
    return LocalStorageBackend(root), root


def test_local_backend_skips_marked_folder(tmp_path):
    backend, _ = _local(tmp_path)

    assert [n["filename"] for n in backend.list_notes()] == ["keyword_ok.md"]
    assert [n["filename"] for n in backend.search("keyword")] == ["keyword_ok.md"]


@pytest.mark.parametrize("action", ["add", "list", "read_repo", "read_path"])
def test_local_backend_refuses_marked_folder(tmp_path, action):
    from notelib.base import StorageError

    backend, root = _local(tmp_path)
    locked = "Finance no open"
    calls = {
        "add": lambda: backend.add(locked, "T", "x", "body", []),
        "list": lambda: backend.list_notes(locked),
        "read_repo": lambda: backend.read("keyword_secret", locked),
        "read_path": lambda: backend.read(str(root / locked / "keyword_secret.md")),
    }

    with pytest.raises(StorageError, match="no open"):
        calls[action]()
