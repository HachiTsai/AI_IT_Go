#!/usr/bin/env python3
"""
Study Notes CLI - 跨專案通用學習筆記管理工具（入口）

實作已拆成 notelib/ 模組：
  common         共用工具（不依賴雲端）
  local_backend  本機 Markdown 後端（預設可獨立運作）
  drive_backend  gdrive CLI 後端（只在真的要進 Google Drive 時才匯入）
  mermaid        Mermaid 區塊檢查與選用轉圖

所有存入 Google Drive 的檔案一律採用 Google 原生文件格式 (Google Docs 📄, Sheets 📊, Slides 📽️)。
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from notelib.base import StorageBackend, StorageError  # noqa: E402
from notelib.common import (  # noqa: E402,F401
    DEFAULT_FOLDER_ID,
    FALLBACK_CACHE_DIR,
    find_gdrive_bin,
    get_current_repo_name,
    sanitize_filename,
)
from notelib.local_backend import LocalStorageBackend  # noqa: E402
from notelib import mermaid  # noqa: E402

_LAZY_DRIVE_NAMES = {"GDriveCliStorageBackend", "WORKSPACE_MIME_TYPES", "WORKSPACE_TYPE_NAMES"}


def __getattr__(name):
    """舊程式碼 `from note import GDriveCliStorageBackend` 仍可用，且只在用到時才匯入 Drive 模組。"""
    if name in _LAZY_DRIVE_NAMES:
        from notelib import drive_backend

        return getattr(drive_backend, name)
    raise AttributeError(f"module 'note' has no attribute {name!r}")


def select_backend() -> StorageBackend:
    """
    自動判定最適合的儲存後端。
    只要系統中具備已授權的 gdrive CLI，才匯入並採用 GDriveCliStorageBackend，
    以確保建立 Google 原生文件格式；否則完全不載入 Drive 模組。
    """
    gdrive_bin = find_gdrive_bin()
    folder_id = os.environ.get("AGENT_STUDY_NOTES_FOLDER_ID", DEFAULT_FOLDER_ID)
    if gdrive_bin:
        from notelib.drive_backend import GDriveCliStorageBackend

        return GDriveCliStorageBackend(gdrive_bin, folder_id)

    env_dir = os.environ.get("AGENT_STUDY_NOTES_DIR")
    if env_dir:
        return LocalStorageBackend(Path(env_dir))

    # 不再自動寫入 Google Drive 同步資料夾：那裡的 .md 會以純文字上傳，而非 Google 原生文件
    print(
        f"⚠️ 未偵測到 gdrive CLI，筆記只存本機暫存，不會同步到 Google Drive: {FALLBACK_CACHE_DIR}",
        file=sys.stderr,
    )
    return LocalStorageBackend(FALLBACK_CACHE_DIR)


def report_mermaid_problems(markdown: str) -> int:
    """把 Mermaid 檢查結果印到 stderr，回傳有問題的區塊數。"""
    bad = 0
    for block in mermaid.check_markdown(markdown):
        if block.issues:
            bad += 1
            print(
                f"⚠️ Mermaid 區塊 #{block.index}（第 {block.start_line} 行）：" + "；".join(block.issues),
                file=sys.stderr,
            )
    return bad


def build_embedded_html(markdown_text: str, title: str) -> str:
    """mermaid 區塊轉成內嵌圖片，整份 Markdown 轉成完整 HTML。"""
    import tempfile

    from notelib.html_export import markdown_to_html

    with tempfile.TemporaryDirectory(prefix="note-mermaid-") as tmp:
        embedded = mermaid.embed_images(markdown_text, Path(tmp))
    return markdown_to_html(embedded, title)


def run_mermaid_command(args) -> int:
    path = Path(args.file)
    if not path.is_file():
        print(f"錯誤: 找不到檔案 {args.file}", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    if args.mermaid_command == "check":
        blocks = mermaid.check_markdown(text)
        if not blocks:
            print("沒有找到 ```mermaid 區塊。")
            return 0
        bad = report_mermaid_problems(text)
        print(f"共 {len(blocks)} 個 Mermaid 區塊，{bad} 個有問題。")
        return 1 if bad else 0
    if args.mermaid_command == "embed":
        try:
            html_text = build_embedded_html(text, args.title or path.stem)
        except (RuntimeError, ValueError) as exc:
            print(f"錯誤: {exc}", file=sys.stderr)
            return 1
        Path(args.out).write_text(html_text, encoding="utf-8")
        print(f"已產生 {args.out}（{len(html_text) // 1024} KB）")
        return 0
    try:
        produced = mermaid.render_blocks(text, Path(args.out), fmt=args.format)
    except (RuntimeError, ValueError) as exc:
        print(f"錯誤: {exc}", file=sys.stderr)
        return 1
    for p in produced:
        print(f"已產生 {p}")
    if not produced:
        print("沒有找到 ```mermaid 區塊。")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Study Notes CLI - 跨專案通用學習筆記管理工具 (支援 Google Docs/Sheets/Slides 原生格式)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    parser_add = subparsers.add_parser("add", help="新增一則學習筆記至 Google Drive")
    parser_add.add_argument("--category", "-c", required=True, help="筆記類別 (例: GCP, Architecture, BugFix)")
    parser_add.add_argument("--title", "-t", required=True, help="筆記標題 (例: Slack_Webhook_Fix)")
    parser_add.add_argument("--tags", help="標籤列表，以逗號分隔 (例: gcp,slack,webhook)")
    parser_add.add_argument("--content", help="筆記內文 (Markdown 格式)")
    parser_add.add_argument("--content-file", help="從指定的 Markdown 檔案讀取筆記內文")
    parser_add.add_argument("--repo", help="指定專案名稱 (預設自動偵測 Git repo)")
    parser_add.add_argument(
        "--format",
        choices=["doc", "sheet", "slide"],
        default="doc",
        help="Google Workspace 格式：doc (Google 文件 📄，預設), sheet (Google 試算表 📊), slide (Google 簡報 📽️)",
    )

    parser_add.add_argument(
        "--mermaid-strict",
        action="store_true",
        help="內文中的 ```mermaid 區塊檢查有問題時中止（預設只警告，仍照常儲存）",
    )

    parser_add.add_argument(
        "--mermaid-mode",
        choices=["keep", "image"],
        default="keep",
        help="keep：mermaid 區塊保留為程式碼（預設）；image：轉成圖片內嵌後以 HTML 上傳成 Google 文件（需 mmdc）",
    )

    # Mermaid command（純本機，不會載入 Drive 模組）
    parser_mm = subparsers.add_parser("mermaid", help="Mermaid 區塊檢查／轉圖（不需要 Drive）")
    mm_sub = parser_mm.add_subparsers(dest="mermaid_command", required=True)
    mm_check = mm_sub.add_parser("check", help="檢查 Markdown 檔中的 ```mermaid 區塊")
    mm_check.add_argument("file", help="Markdown 檔案路徑")
    mm_embed = mm_sub.add_parser("embed", help="轉圖並內嵌成 HTML（可直接上傳 Drive 轉成 Google 文件）")
    mm_embed.add_argument("file", help="Markdown 檔案路徑")
    mm_embed.add_argument("--out", required=True, help="輸出 HTML 檔路徑")
    mm_embed.add_argument("--title", help="HTML 標題（預設用檔名）")
    mm_render = mm_sub.add_parser("render", help="用 mermaid-cli (mmdc) 把區塊轉成圖檔")
    mm_render.add_argument("file", help="Markdown 檔案路徑")
    mm_render.add_argument("--out", required=True, help="輸出資料夾")
    mm_render.add_argument("--format", choices=["png", "svg"], default="png")

    # Search command
    parser_search = subparsers.add_parser("search", help="搜尋既有筆記")
    parser_search.add_argument("query", help="搜尋關鍵字")
    parser_search.add_argument("--repo", help="限定在特定 repo 內搜尋")

    # Read command
    parser_read = subparsers.add_parser("read", help="讀取筆記內容")
    parser_read.add_argument("identifier", help="筆記標題、檔名或 Drive File ID")
    parser_read.add_argument("--repo", help="指定專案名稱")

    # List command
    parser_list = subparsers.add_parser("list", help="列出所有筆記")
    parser_list.add_argument("--repo", help="限定特定 repo")

    args = parser.parse_args()

    if args.command == "mermaid":
        sys.exit(run_mermaid_command(args))

    backend = select_backend()
    repo_name = getattr(args, "repo", None) or get_current_repo_name()

    if args.command == "add":
        content = ""
        if args.content_file:
            path = Path(args.content_file)
            if not path.exists():
                print(f"錯誤: 找不到內容檔案 {args.content_file}", file=sys.stderr)
                sys.exit(1)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        elif args.content:
            content = args.content
        else:
            print("錯誤: 必須提供 --content 或 --content-file", file=sys.stderr)
            sys.exit(1)

        if args.format == "doc":
            problems = report_mermaid_problems(content)
            if problems and args.mermaid_strict:
                print("錯誤: Mermaid 檢查未通過，已中止儲存（移除 --mermaid-strict 可僅警告）", file=sys.stderr)
                sys.exit(1)

        html_text = None
        if args.mermaid_mode == "image" and args.format == "doc":
            try:
                html_text = build_embedded_html(content, args.title)
            except (RuntimeError, ValueError) as exc:
                print(f"錯誤: Mermaid 轉圖失敗，已中止儲存：{exc}", file=sys.stderr)
                sys.exit(1)
            if isinstance(backend, LocalStorageBackend):
                print("⚠️ 目前不是 Drive 後端，--mermaid-mode image 不會產生圖片文件，只存 Markdown。", file=sys.stderr)

        tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
        msg, doc_id = backend.add(
            repo=repo_name,
            category=args.category,
            title=args.title,
            content=content,
            tags=tags,
            doc_format=args.format,
            html=html_text,
        )
        print(msg)

    elif args.command == "search":
        results = backend.search(args.query, repo=args.repo)
        if not results:
            print(f"未找到匹配關鍵字 '{args.query}' 的筆記。")
            return
        print(f"🔍 搜尋 '{args.query}' 結果 ({len(results)} 筆):")
        for idx, item in enumerate(results, 1):
            ftype = item.get("type", "檔案")
            print(f"  {idx}. [{item.get('repo', '')}] {item.get('filename', '')} ({ftype})")
            if "snippet" in item:
                print(f"     內文: {item['snippet']}")
            if "id" in item:
                print(f"     Link: https://docs.google.com/document/d/{item['id']}/edit")

    elif args.command == "read":
        text = backend.read(args.identifier, repo=args.repo)
        if text is None:
            print(f"錯誤: 找不到筆記 '{args.identifier}'", file=sys.stderr)
            sys.exit(1)
        print(text)

    elif args.command == "list":
        notes = backend.list_notes(repo=args.repo)
        if not notes:
            target = f"專案 {args.repo}" if args.repo else "所有專案"
            print(f"目前 {target} 中沒有筆記。")
            return
        print(f"📚 學習筆記清單 ({len(notes)} 筆):")
        for idx, item in enumerate(notes, 1):
            ftype = item.get("type", "Google 文件 📄")
            link_hint = f" | ID: {item.get('id')}" if "id" in item else ""
            print(f"  {idx}. [{item.get('repo', '')}] {item.get('filename', '')} [{ftype}] ({item.get('modified', '')}){link_hint}")


if __name__ == "__main__":
    try:
        main()
    except StorageError as exc:
        print(f"錯誤: {exc}", file=sys.stderr)
        sys.exit(1)
