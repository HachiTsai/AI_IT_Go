#!/usr/bin/env python3
"""Structured git commit helper.

Staging control, staged diff summary, closed type list, `git commit -F`,
Co-Authored-By injection, auto-quick mode, push with retry.

Modes:
  committer.py                          stage, then print diff/stat + template for drafting
  committer.py --message-file F         commit with the drafted message, then push
  committer.py --auto-quick             build a short message from the staged files and commit
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence

GIT_TIMEOUT_SEC = 60
GIT_COMMIT_TIMEOUT_SEC = 300
GIT_PUSH_TIMEOUT_SEC = 300
PUSH_BACKOFF_SEC = (2, 4, 8, 16)

COMMIT_TYPES = ("feat", "fix", "refactor", "docs", "test", "style", "chore", "revert", "merge")
COAUTHOR_LINE = "Co-Authored-By: Claude <noreply@anthropic.com>"
COAUTHOR_RE = re.compile(r"^Co-Authored-By:\s*Claude\b", re.M | re.I)
HEADER_RE = re.compile(rf"^({'|'.join(COMMIT_TYPES)})(\([^)]+\))?!?: \S")

FIX_SIGNALS = ("fix", "bug", "repair", "broken", "resolve")
FEAT_SIGNALS = ("feat", "new", "implement")
SCOPE_DOMINANCE = 0.5
AUTO_QUICK_FILE_SOFT_LIMIT = 10

# Paths that must never be committed by accident.
SENSITIVE_PATTERNS = (
    ".env", ".env.*", "*.pem", "*.key", "id_rsa", "id_ed25519",
    "credentials/*", "*/credentials/*", "credentials.json", "secrets.*",
)

TEMPLATE = """\
<type>(<scope>): <short description>

## 核心變更

- 具體改了什麼

## 變更理由

- 為什麼改、解決了什麼問題

## 驗證

- 跑過什麼檢查與結果（純文件變更寫「無需測試—純文件變更」）

## Pending Tasks

- 無
"""


def git(args: Sequence[str], timeout: int = GIT_TIMEOUT_SEC, check: bool = True) -> subprocess.CompletedProcess:
    """Run git; stdout decoded leniently so binary diffs cannot crash the script."""
    result = subprocess.run(["git", *args], capture_output=True, timeout=timeout, check=check)
    result.stdout = result.stdout.decode("utf-8", errors="replace")
    result.stderr = result.stderr.decode("utf-8", errors="replace")
    return result


def staged_files() -> List[str]:
    # core.quotePath=false keeps non-ASCII paths readable instead of octal-escaped.
    out = git(["-c", "core.quotePath=false", "diff", "--staged", "--name-only"]).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def staged_diff() -> str:
    return git(["diff", "--staged", "--", ".", ":(exclude)*.json"]).stdout


def staged_stat() -> str:
    return git(["diff", "--staged", "--stat", "--", ".", ":(exclude)*.json"]).stdout


def current_branch() -> str:
    return git(["branch", "--show-current"]).stdout.strip()


def path_matches(path: str, pattern: str) -> bool:
    """Glob match, or directory-prefix match when pattern is a directory."""
    return fnmatch.fnmatch(path, pattern) or path.startswith(pattern.rstrip("/") + "/")


def find_sensitive(files: Sequence[str]) -> List[str]:
    hits = []
    for f in files:
        name = Path(f).name
        if any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(f, p) for p in SENSITIVE_PATTERNS):
            hits.append(f)
    return hits


def run_git_add(paths: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> bool:
    """`paths` -> stage only those; otherwise `git add .` then unstage `exclude`."""
    try:
        if paths:
            git(["reset", "-q"], check=False)
            git(["add", "--", *paths])
            return True
        git(["add", "."])
        if exclude:
            git(["reset", "-q", "--", *exclude], check=False)
            status = git(["status", "--porcelain"]).stdout
            left = [l[3:] for l in status.splitlines() if l.startswith("??")
                    and any(path_matches(l[3:], e) for e in exclude)]
            if left:
                print("⚠️ 排除路徑下仍有未追蹤檔案（保持未暫存）：", *left[:10], sep="\n   - ")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ [Git] 暫存失敗：{e}", file=sys.stderr)
        return False


def infer_scope(files: Sequence[str]) -> str:
    """Top-level directory when it covers at least half of the files, else 'project'."""
    counts: dict = {}
    for f in files:
        parts = Path(f.replace("\\", "/")).parts
        if len(parts) > 1:
            counts[parts[0]] = counts.get(parts[0], 0) + 1
    if not counts:
        return "project"
    top, n = max(counts.items(), key=lambda kv: kv[1])
    tied = sum(1 for v in counts.values() if v == n) > 1
    if tied or n < len(files) * SCOPE_DOMINANCE:
        return "project"
    return top.lstrip(".") or "project"


def is_test_file(path: str) -> bool:
    p = Path(path)
    name = p.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or "tests" in p.parts


def infer_commit_type(files: Sequence[str], diff: str) -> str:
    """Conservative guess; falls back to 'chore'."""
    code = [f for f in files if Path(f).suffix.lower() != ".md"]
    if files and not code:
        return "docs"
    diff_lower = (diff or "").lower()
    names = " ".join(Path(f).name.lower() for f in code)
    if any(re.search(rf"\b{s}\b", diff_lower) or re.search(rf"\b{s}\b", names) for s in FIX_SIGNALS):
        return "fix"
    if files and sum(is_test_file(f) for f in files) >= len(files) * 0.5:
        return "test"
    if any(re.search(rf"\b{s}\b", diff_lower) for s in FEAT_SIGNALS):
        return "feat"
    return "chore"


def build_quick_message(files: Sequence[str], diff: str) -> str:
    if not files:
        raise ValueError("no staged files")
    scope = infer_scope(files)
    ctype = infer_commit_type(files, diff)
    bullet = f"Update `{files[0]}`" if len(files) == 1 else f"Update {len(files)} files under `{scope}`"
    return f"{ctype}({scope}): update {scope}\n\n- {bullet}\n\n{COAUTHOR_LINE}\n"


def ensure_coauthor_line(msg: str) -> str:
    """Append Co-Authored-By unless already present (idempotent)."""
    if COAUTHOR_RE.search(msg):
        return msg
    nl = "\r\n" if "\r\n" in msg else "\n"
    return msg.rstrip("\r\n") + nl * 2 + COAUTHOR_LINE + nl


def push_with_retry(branch: str) -> bool:
    """`git push -u origin <branch>`; retry network failures with 2/4/8/16s backoff."""
    for attempt in range(len(PUSH_BACKOFF_SEC) + 1):
        try:
            git(["push", "-u", "origin", branch], timeout=GIT_PUSH_TIMEOUT_SEC)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            if attempt == len(PUSH_BACKOFF_SEC):
                print(f"❌ [Git] 推送失敗：{e}", file=sys.stderr)
                return False
            wait = PUSH_BACKOFF_SEC[attempt]
            print(f"⚠️ 推送失敗，{wait}s 後重試（{attempt + 1}/{len(PUSH_BACKOFF_SEC)}）")
            time.sleep(wait)
    return False


def finalize_commit(message_file: Path, no_push: bool = False, dry_run: bool = False) -> int:
    if not message_file.exists():
        print(f"❌ 找不到訊息檔：{message_file}", file=sys.stderr)
        return 1
    msg = message_file.read_text(encoding="utf-8")
    if not msg.strip():
        print("❌ Commit message 為空。", file=sys.stderr)
        return 1
    if not HEADER_RE.match(msg):
        print(f"❌ 標題需為 `<type>(<scope>): <描述>`，type 限：{', '.join(COMMIT_TYPES)}", file=sys.stderr)
        return 1

    signed = ensure_coauthor_line(msg)
    if signed != msg and not dry_run:
        with message_file.open("w", encoding="utf-8", newline="") as fh:
            fh.write(signed)
    msg = signed

    if dry_run:
        print("🧪 [Dry Run] 將以下列訊息提交：\n" + "-" * 60 + f"\n{msg}\n" + "-" * 60)
        print("🧪 [Dry Run] 提交後不會推送。" if no_push else "🧪 [Dry Run] 提交後會推送。")
        return 0

    try:
        git(["commit", "-F", str(message_file)], timeout=GIT_COMMIT_TIMEOUT_SEC)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        detail = getattr(e, "stderr", "") or getattr(e, "stdout", "") or ""
        print(f"❌ [Git] 提交失敗：{e}\n{detail}", file=sys.stderr)
        return 1
    print(f"✅ 已提交：{git(['log', '--oneline', '-1']).stdout.strip()}")

    if no_push:
        print("⏭️ 已用 --no-push 略過推送。")
        return 0
    if not push_with_retry(current_branch()):
        return 1
    print("🚀 已推送。")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--message-file", type=Path, help="已草擬好的訊息檔，直接 git commit -F")
    ap.add_argument("--auto-quick", action="store_true", help="自動產生精簡訊息並提交（限小型變更）")
    ap.add_argument("--no-push", action="store_true", help="提交後不推送")
    ap.add_argument("--dry-run", action="store_true", help="只預覽，不提交")
    ap.add_argument("--no-stage", action="store_true", help="不執行 git add，使用既有暫存區")
    ap.add_argument("--stage-list", nargs="+", metavar="PATH", help="只暫存指定路徑")
    ap.add_argument("--exclude", nargs="+", metavar="PATH", help="git add . 後排除的路徑")
    ap.add_argument("--allow-sensitive", action="store_true", help="略過敏感檔案檢查")
    args = ap.parse_args(argv)

    if args.message_file and args.auto_quick:
        ap.error("--message-file 與 --auto-quick 互斥")

    try:
        if not args.no_stage and not run_git_add(args.stage_list, args.exclude):
            return 1
        files = staged_files()
        if not files:
            print("⚠️ 暫存區沒有變更，無可提交內容。")
            return 1

        if not args.allow_sensitive:
            hits = find_sensitive(files)
            if hits:
                print("❌ 暫存區含疑似敏感檔案，已中止：", *hits, sep="\n   - ", file=sys.stderr)
                print("   確認無誤請加 --allow-sensitive；否則 `git reset HEAD -- <path>` 移出暫存。", file=sys.stderr)
                return 1

        message_file = args.message_file
        if args.auto_quick:
            if len(files) > AUTO_QUICK_FILE_SOFT_LIMIT:
                print(f"⚠️ 暫存 {len(files)} 檔，超過 {AUTO_QUICK_FILE_SOFT_LIMIT}；--auto-quick 僅適合小型變更，建議改走互動式提交。")
            message_file = Path(git(["rev-parse", "--git-path", "COMMIT_MSG_TEMP"]).stdout.strip())
            message_file.write_text(build_quick_message(files, staged_diff()), encoding="utf-8")

        if message_file is None:
            print(f"📋 Staged 檔案（{len(files)}）：\n   " + "\n   ".join(files))
            print("\n📊 統計：\n" + staged_stat())
            print("📝 Diff（已排除 *.json）：\n" + staged_diff())
            print("-" * 60 + "\n請依下列模板草擬訊息，寫入 .git/COMMIT_MSG_TEMP 後執行：")
            print("  python .claude/skills/commit-workflow/scripts/committer.py --message-file .git/COMMIT_MSG_TEMP --no-stage\n")
            print(f"Type 限：{', '.join(COMMIT_TYPES)}\n" + "-" * 60 + "\n" + TEMPLATE)
            return 0

        rc = finalize_commit(message_file, no_push=args.no_push, dry_run=args.dry_run)
        if rc == 0 and message_file.exists() and (args.auto_quick or not args.dry_run):
            message_file.unlink()
        return rc
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ [Git] 指令失敗：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
