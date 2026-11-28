import struct
import subprocess
import sys
import zlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
import note  # noqa: E402
from notelib import mermaid  # noqa: E402
from notelib.html_export import markdown_to_html, strip_frontmatter  # noqa: E402

MD = """---
title: "t"
---

# 標題

```mermaid
flowchart TD
  A --> B
```

```python
print(1)
```

```mermaid
sequenceDiagram
  A->>B: hi
```
"""


def make_png(path: Path, w: int, h: int) -> Path:
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + b"\xff\xff\xff" * w for _ in range(h))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return path


def fake_render(sizes):
    def _render(markdown, out_dir, fmt="png"):
        out_dir.mkdir(parents=True, exist_ok=True)
        return [make_png(out_dir / f"d{i}.png", w, h) for i, (w, h) in enumerate(sizes, 1)]

    return _render


def test_png_size_and_rejects_non_png(tmp_path):
    assert mermaid.png_size(make_png(tmp_path / "a.png", 7, 3)) == (7, 3)
    (tmp_path / "x.png").write_bytes(b"not a png at all, just text here")
    with pytest.raises(ValueError):
        mermaid.png_size(tmp_path / "x.png")


def test_embed_replaces_only_mermaid_blocks_and_scales(tmp_path):
    # 2 倍縮放：1440x400 → 顯示 720x200，超過 620 寬 → 縮到 620；第二張 400x2000 → 200x1000 → 高度限 700
    with patch.object(mermaid, "render_blocks", fake_render([(1440, 400), (400, 2000)])):
        out = mermaid.embed_images(MD, tmp_path)
    assert out.count("<img") == 2
    assert "```mermaid" not in out
    assert "```python" in out and "print(1)" in out  # 其他區塊不動
    assert 'width="620"' in out
    assert 'height="700"' in out and 'width="140"' in out


def test_embed_without_blocks_is_noop(tmp_path):
    assert mermaid.embed_images("# 只有文字\n", tmp_path) == "# 只有文字\n"


def test_markdown_to_html_strips_frontmatter_and_keeps_img():
    html = markdown_to_html("---\ntitle: x\n---\n\n# H\n\n<p><img src=\"data:image/png;base64,AAAA\"></p>\n", "T")
    assert "title: x" not in html
    assert "<h1>H</h1>" in html and "<img" in html and "<title>T</title>" in html
    assert strip_frontmatter("沒有 frontmatter") == "沒有 frontmatter"


def test_build_embedded_html_end_to_end_with_fake_render():
    with patch.object(mermaid, "render_blocks", fake_render([(400, 200), (400, 200)])):
        html = note.build_embedded_html(MD, "T")
    assert html.count("<img") == 2 and "<h1>標題</h1>" in html


def test_drive_backend_uploads_html_as_google_doc(tmp_path):
    from notelib.drive_backend import GDriveCliStorageBackend

    gd = GDriveCliStorageBackend("gdrive", "folder")
    calls = []

    def run(args):
        calls.append(args)
        if args[:2] == ["mutate", "upload"]:
            uploaded = Path(args[2])
            assert uploaded.suffix == ".html"
            assert "<img" in uploaded.read_text(encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, stdout='{"id": "FILEID"}', stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    gd._run_gdrive = MagicMock(side_effect=run)
    gd._get_or_create_repo_folder = MagicMock(return_value="repo-folder")
    with patch("pathlib.Path.home", return_value=tmp_path):
        msg, _ = gd.add("R", "Tools", "T", "# md", [], doc_format="doc", html="<html><img src='x'></html>")
    upload = next(c for c in calls if c[:2] == ["mutate", "upload"])
    assert "application/vnd.google-apps.document" in upload
    assert "成功建立" in msg


def test_cli_image_mode_failure_aborts_without_saving(tmp_path):
    f = tmp_path / "n.md"
    f.write_text("```mermaid\nflowchart TD\n  A --> B\n```\n", encoding="utf-8")
    env = {"AGENT_STUDY_NOTES_DIR": str(tmp_path / "notes"), "HOME": str(tmp_path),
           "PATH": "/usr/bin:/bin", "MMDC_BIN": "/nonexistent"}
    res = subprocess.run(
        [sys.executable, str(SCRIPTS / "note.py"), "add", "-c", "T", "-t", "x", "--content-file", str(f),
         "--mermaid-mode", "image", "--repo", "R"],
        capture_output=True, text=True, env=env,
    )
    assert res.returncode == 1
    assert "mmdc" in res.stderr
    assert not (tmp_path / "notes" / "R").exists()
