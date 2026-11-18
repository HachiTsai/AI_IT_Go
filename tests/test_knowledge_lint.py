import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from knowledge_lint import lint


def make(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


GOOD = "---\ntitle: A\nsources:\n  - knowledge/raw/s.md\nupdated: 2026-11-18\n---\n"


class TestKnowledgeLint(unittest.TestCase):
    def test_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, "knowledge/raw/s.md", "hello world")
            make(root, "knowledge/wiki/index.md", GOOD.replace("A", "I") + "[[a]]")
            make(root, "knowledge/wiki/a.md", GOOD + '> "hello world" — knowledge/raw/s.md\n')
            self.assertEqual(lint(root), [])

    def test_problems(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            make(root, "knowledge/raw/s.md", "hello world")
            make(root, "knowledge/wiki/a.md", GOOD + '[[nope]] TODO\n> "fake" — knowledge/raw/s.md\n')
            make(root, "knowledge/wiki/b.md", "no front matter")
            out = "\n".join(lint(root))
            for kw in ("連結無效", "TODO", "逐字", "缺少 front matter", "孤立"):
                self.assertIn(kw, out)


if __name__ == "__main__":
    unittest.main()
