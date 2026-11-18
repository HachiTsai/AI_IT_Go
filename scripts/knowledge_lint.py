"""knowledge/wiki 結構檢查（不含 AI）：front matter、來源存在、連結有效、引用逐字、TODO。"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("title", "sources", "updated")
LINK_RE = re.compile(r"\[\[([^\]|#]+)")
QUOTE_RE = re.compile(r'^>\s*"(.+?)"\s*[—-]+\s*(\S+)\s*$', re.M)


def parse_front_matter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    meta: dict = {}
    key = None
    for line in m.group(1).splitlines():
        if line.startswith("  - ") and key:
            meta[key].append(line[4:].strip())
        elif ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val in ("", "[]"):
                meta[key] = []
            else:
                meta[key] = val
    return meta


def lint(root: Path = ROOT) -> list[str]:
    wiki = root / "knowledge" / "wiki"
    problems: list[str] = []
    pages = sorted(wiki.glob("*.md")) if wiki.is_dir() else []
    names = {p.stem for p in pages}
    linked: set[str] = set()
    for page in pages:
        rel = page.relative_to(root)
        text = page.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        for key in REQUIRED:
            if key not in meta:
                problems.append(f"{rel}: 缺少 front matter 欄位 {key}")
        sources = meta.get("sources", [])
        for src in sources if isinstance(sources, list) else []:
            if not (root / src).is_file():
                problems.append(f"{rel}: 來源不存在 {src}")
        for target in LINK_RE.findall(text):
            target = target.strip()
            linked.add(target)
            if target not in names:
                problems.append(f"{rel}: 連結無效 [[{target}]]")
        for quote, src in QUOTE_RE.findall(text):
            src_path = root / src
            if not src_path.is_file():
                problems.append(f"{rel}: 引用來源不存在 {src}")
            elif quote not in src_path.read_text(encoding="utf-8"):
                problems.append(f"{rel}: 引用未逐字出現在 {src}")
        if "TODO" in text:
            problems.append(f"{rel}: 含 TODO")
    for page in pages:
        if page.stem != "index" and page.stem not in linked:
            problems.append(f"{page.relative_to(root)}: 孤立頁面（沒有任何連結指向它）")
    return problems


def main() -> int:
    problems = lint()
    for p in problems:
        print(p)
    print(f"{len(problems)} 個問題" if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
