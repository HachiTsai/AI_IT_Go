import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
from notelib import mermaid  # noqa: E402

GOOD = "# 標題\n\n```mermaid\nflowchart TD\n  A[開始] --> B(結束)\n```\n"


def test_extract_and_validate_good_block():
    blocks = mermaid.check_markdown(GOOD)
    assert len(blocks) == 1
    assert blocks[0].start_line == 3
    assert blocks[0].issues == []


def test_frontmatter_and_comments_are_skipped():
    md = "```mermaid\n---\ntitle: t\n---\n%% note\nsequenceDiagram\n  A->>B: hi\n```\n"
    assert mermaid.check_markdown(md)[0].issues == []


@pytest.mark.parametrize(
    "md, fragment",
    [
        ("```mermaid\nflowchart TD\n  A --> B\n", "沒有閉合"),
        ("```mermaid\n```\n", "空的"),
        ("```mermaid\nhello world\n```\n", "不是已知"),
        ("```mermaid\nflowchart TD\n  A[open --> B\n```\n", "括號"),
    ],
)
def test_detects_definite_problems(md, fragment):
    issues = mermaid.check_markdown(md)[0].issues
    assert any(fragment in i for i in issues)


def test_bare_fence_with_diagram_declaration_is_recognised():
    # Google 文件匯出 md 後，```mermaid 會變成無標籤的 ```
    md = "```\nflowchart TD\n  A --> B\n```\n\n```py\nprint(1)\n```\n\n```\n普通文字\n```\n"
    blocks = mermaid.check_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].issues == []


def test_non_mermaid_fences_ignored():
    assert mermaid.extract_blocks("```python\nprint(1)\n```\n") == []


def test_render_without_mmdc_is_explicit(tmp_path):
    with patch.object(mermaid, "find_mmdc", return_value=None):
        with pytest.raises(RuntimeError, match="mmdc"):
            mermaid.render_blocks(GOOD, tmp_path)


def test_render_rejects_invalid_block(tmp_path):
    with patch.object(mermaid, "find_mmdc", return_value="/bin/true"):
        with pytest.raises(ValueError):
            mermaid.render_blocks("```mermaid\nnope\n```\n", tmp_path)


def test_cli_check_and_strict_add(tmp_path):
    good = tmp_path / "good.md"
    good.write_text(GOOD, encoding="utf-8")
    bad = tmp_path / "bad.md"
    bad.write_text("```mermaid\nnope\n```\n", encoding="utf-8")
    note = str(SCRIPTS / "note.py")
    env = {"AGENT_STUDY_NOTES_DIR": str(tmp_path / "notes"), "PATH": "/usr/bin:/bin"}

    assert subprocess.run([sys.executable, note, "mermaid", "check", str(good)], capture_output=True, env=env).returncode == 0
    assert subprocess.run([sys.executable, note, "mermaid", "check", str(bad)], capture_output=True, env=env).returncode == 1

    strict = subprocess.run(
        [sys.executable, note, "add", "-c", "T", "-t", "bad", "--content-file", str(bad), "--mermaid-strict", "--repo", "R"],
        capture_output=True, text=True, env=env,
    )
    assert strict.returncode == 1
    assert not (tmp_path / "notes" / "R").exists()

    lenient = subprocess.run(
        [sys.executable, note, "add", "-c", "T", "-t", "bad", "--content-file", str(bad), "--repo", "R"],
        capture_output=True, text=True, env=env,
    )
    assert lenient.returncode == 0
    assert "Mermaid" in lenient.stderr
    saved = (tmp_path / "notes" / "R" / "T_bad.md").read_text(encoding="utf-8")
    assert "```mermaid" in saved


def test_mermaid_command_does_not_import_drive_module(tmp_path):
    f = tmp_path / "g.md"
    f.write_text(GOOD, encoding="utf-8")
    code = (
        "import sys; sys.argv=['note','mermaid','check',%r]; sys.path.insert(0,%r); import note\n"
        "try:\n note.main()\nexcept SystemExit: pass\n"
        "assert 'notelib.drive_backend' not in sys.modules, 'drive module was imported'\n"
    ) % (str(f), str(SCRIPTS))
    assert subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).returncode == 0
