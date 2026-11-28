"""gdrive CLI 後端：只有真的要進 Google Drive 時才會被匯入。"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import NoOpenError, StorageBackend, StorageError
from .common import ensure_folder_allowed, format_note, is_no_open, note_stem, sanitize_filename

# Google Workspace 原生 MIME 類型映射
WORKSPACE_MIME_TYPES = {
    "doc": "application/vnd.google-apps.document",
    "sheet": "application/vnd.google-apps.spreadsheet",
    "slide": "application/vnd.google-apps.presentation",
}

WORKSPACE_TYPE_NAMES = {
    "application/vnd.google-apps.document": "Google Doc 📄",
    "application/vnd.google-apps.spreadsheet": "Google Sheet 📊",
    "application/vnd.google-apps.presentation": "Google Slide 📽️",
    "application/vnd.google-apps.folder": "Google Folder 📁",
}


def _extract_id(stdout: str) -> str:
    """從 gdrive 輸出取出檔案／資料夾 ID：文字格式 `(ID: x)` 或 JSON 的 id；取不到回傳空字串。"""
    m = re.search(r"\(ID:\s*([^\)\s]+)\)", stdout)
    if m:
        return m.group(1)
    try:
        return json.loads(stdout.strip()).get("id", "")
    except (ValueError, AttributeError):
        return ""


class GDriveCliStorageBackend(StorageBackend):
    """
    透過 gdrive CLI 直接在雲端建立與管理 Google 原生文件格式 (Docs, Sheets, Slides)。
    """
    def __init__(self, gdrive_bin: str, folder_id: str):
        self.gdrive_bin = gdrive_bin
        self.folder_id = folder_id

    def _run_gdrive(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = [self.gdrive_bin] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def _query_list(self, args: List[str], error: str) -> List[Dict]:
        """執行回傳 JSON 清單的唯讀查詢；失敗丟 StorageError，不可當成沒有結果。"""
        res = self._run_gdrive(args)
        if res.returncode != 0:
            raise StorageError(f"{error}：{res.stderr.strip()}")
        try:
            items = json.loads(res.stdout.strip() or "[]")
        except ValueError:
            items = None
        if not isinstance(items, list):
            raise StorageError(f"{error}：輸出不是清單: {res.stdout.strip()[:200]!r}")
        return items

    def _list_items(self, folder_id: str) -> List[Dict]:
        """列出資料夾內容。"""
        return self._query_list(["readonly", "ls", folder_id, "--json"], "查詢 Drive 清單失敗")

    def _find_repo_folder(self, repo: str) -> Optional[str]:
        """在筆記根目錄找 repo 資料夾；確定沒有才回傳 None。

        清單查不到時丟 StorageError：不知道資料夾在不在就建立，會產生同名資料夾。
        """
        ensure_folder_allowed(repo)
        try:
            items = self._list_items(self.folder_id)
        except StorageError as exc:
            raise StorageError(f"無法取得 Drive 資料夾「{repo}」，已中止：{exc}") from exc
        for item in items:
            if item.get("name") == repo and item.get("mimeType") == "application/vnd.google-apps.folder":
                return item["id"]
        return None

    def _get_or_create_repo_folder(self, repo: str) -> str:
        existing = self._find_repo_folder(repo)
        if existing:
            return existing

        res_mkdir = self._run_gdrive(["mutate", "mkdir", repo, "--parent", self.folder_id, "--json"])
        folder_id = _extract_id(res_mkdir.stdout) if res_mkdir.returncode == 0 else ""
        if folder_id:
            return folder_id

        # 不可退回根目錄：筆記會放錯位置卻回報成功
        detail = res_mkdir.stderr.strip() or f"mkdir 輸出中找不到 ID: {res_mkdir.stdout.strip()!r}"
        raise StorageError(f"無法取得 Drive 資料夾「{repo}」，已中止：{detail}")

    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
        html: Optional[str] = None,
    ) -> Tuple[str, str]:
        repo_folder_id = self._get_or_create_repo_folder(repo)
        clean_title = note_stem(category, title)

        # html 只用於 Google 文件：base64 內嵌圖片靠 HTML 匯入才會保留
        use_html = bool(html) and doc_format == "doc"
        clean_ext = ".csv" if doc_format == "sheet" else (".html" if use_html else ".md")
        temp_name = f"{clean_title}{clean_ext}"

        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / temp_name

        formatted = format_note(repo, category, title, content, tags)
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html if use_html else formatted)

        # 決定 Google Workspace MIME 類型
        target_mime = WORKSPACE_MIME_TYPES.get(doc_format, WORKSPACE_MIME_TYPES["doc"])

        # 上傳並要求 Google Drive 轉換為原生文件格式
        upload_cmd = [
            "mutate", "upload", str(temp_file),
            "--mime-type", target_mime,
            "--parent", repo_folder_id,
            "--json"
        ]
        res = self._run_gdrive(upload_cmd)

        if res.returncode != 0:
            raise StorageError(
                f"上傳 Google Drive 失敗：{res.stderr.strip()}\n待上傳的內容保留在暫存檔: {temp_file}"
            )

        # 從回傳中提取 File ID
        file_id = _extract_id(res.stdout)

        doc_url = ""
        if file_id:
            # 重新命名為無副檔名之 Google 文件標準標題
            self._run_gdrive(["mutate", "rename", file_id, clean_title])
            # 取得網頁檢視 URL
            url_res = self._run_gdrive(["readonly", "url", file_id])
            doc_url = url_res.stdout.strip()

        # 本機快照一律存放於系統快取目錄 (~/.cache/agent_study_notes)，絕不寫入 Google Drive 本機同步目錄以防自動上傳 .md
        cache_dir = Path.home() / ".cache" / "agent_study_notes" / sanitize_filename(repo)
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            local_cache = cache_dir / f"{clean_title}.md"
            with open(local_cache, "w", encoding="utf-8") as f:
                f.write(formatted)
        except Exception:
            pass

        type_label = WORKSPACE_TYPE_NAMES.get(target_mime, "Google 文件")
        link_str = doc_url or (f"https://docs.google.com/document/d/{file_id}/edit" if file_id else "")
        return (
            f"成功建立 {type_label} 並存入 Google Drive: {clean_title}\n連結: {link_str}",
            link_str or file_id,
        )

    @staticmethod
    def _notes_in(repo: str, items: List[Dict]) -> List[Dict]:
        """從資料夾內容挑出筆記（Google Workspace 文件與 .md），略過子資料夾與其他檔案。"""
        notes = []
        for item in items:
            mime = item.get("mimeType", "")
            if mime == "application/vnd.google-apps.folder":
                continue
            if mime in WORKSPACE_TYPE_NAMES or item.get("name", "").endswith(".md"):
                notes.append(
                    {
                        "repo": repo,
                        "filename": item.get("name"),
                        "type": WORKSPACE_TYPE_NAMES.get(mime, "Markdown 📝"),
                        "id": item.get("id"),
                        "modified": item.get("modifiedTime", ""),
                    }
                )
        return notes

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        notes = []
        if repo:
            target_folders = [(repo, self._get_or_create_repo_folder(repo))]
        else:
            # 遍歷所有 repo 資料夾以列出真正的筆記文件
            target_folders = [
                (item.get("name"), item.get("id"))
                for item in self._list_items(self.folder_id)
                if item.get("mimeType") == "application/vnd.google-apps.folder" and not is_no_open(item.get("name"))
            ]

        for r_name, f_id in target_folders:
            notes.extend(self._notes_in(r_name, self._list_items(f_id)))
        notes.sort(key=lambda x: (x["repo"], x["filename"]))
        return notes

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        """依檔名搜尋筆記資料夾（根目錄與各 repo 子資料夾）；不搜尋 Drive 其他位置，也不建立資料夾。"""
        if repo:
            folder_id = self._find_repo_folder(repo)
            notes = self._notes_in(repo, self._list_items(folder_id)) if folder_id else []
        else:
            root_items = self._list_items(self.folder_id)
            notes = self._notes_in("根目錄", root_items)
            for item in root_items:
                if item.get("mimeType") == "application/vnd.google-apps.folder" and not is_no_open(item.get("name")):
                    notes.extend(self._notes_in(item.get("name"), self._list_items(item.get("id"))))

        keyword = query.lower()
        results = [
            {**note, "snippet": f"匹配 Drive {note['type']}: {note['filename']}"}
            for note in notes
            if keyword in note["filename"].lower()
        ]
        results.sort(key=lambda x: (x["repo"], x["filename"]))
        return results

    def _ensure_readable(self, file_id: str) -> None:
        """直接用 ID 讀取前，只查 metadata 逐層確認不在 no open 資料夾內；查不到就不讀。"""
        pending, seen = [file_id], set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            res = self._run_gdrive(["readonly", "info", current, "--json"])
            try:
                info = json.loads(res.stdout) if res.returncode == 0 else None
                name = info["name"]
            except (ValueError, KeyError, TypeError):
                raise StorageError(f"找不到筆記，或無法確認「{file_id}」的上層資料夾，未讀取：{res.stderr.strip()}")
            if current == file_id and info.get("mimeType") == "application/vnd.google-apps.shortcut":
                raise StorageError(f"「{file_id}」是捷徑，無法確認目標位置，未讀取；請改用目標檔案的 ID")
            if current != file_id or info.get("mimeType") == "application/vnd.google-apps.folder":
                ensure_folder_allowed(name)
            pending.extend(info.get("parents") or [])

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        if repo:
            ensure_folder_allowed(repo)
        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        out_file = temp_dir / "read_note.md"

        file_id = identifier

        # 優先從清單中依檔名或 ID 比對
        matched_id = None
        # 清單查不到時仍嘗試把 identifier 當檔案 ID 讀取；也讀不到才回報查詢錯誤
        listing_error = None
        try:
            all_notes = self.list_notes(repo)
        except StorageError as exc:
            all_notes, listing_error = [], exc

        # 1. 精確比對檔名或 ID
        for n in all_notes:
            if n["filename"] == identifier or n.get("id") == identifier:
                matched_id = n.get("id")
                break

        # 2. 忽略大小寫比對檔名
        if not matched_id:
            for n in all_notes:
                if n["filename"].lower() == identifier.lower():
                    matched_id = n.get("id")
                    break

        # 3. 部分比對檔名
        if not matched_id:
            for n in all_notes:
                if identifier.lower() in n["filename"].lower():
                    matched_id = n.get("id")
                    break

        if matched_id:
            file_id = matched_id  # 清單已略過 no open 資料夾
        else:
            try:
                self._ensure_readable(file_id)
            except StorageError as exc:
                # 清單查詢本身失敗時回報查詢錯誤；no open 的拒絕一律照實回報
                if listing_error and not isinstance(exc, NoOpenError):
                    raise listing_error from exc
                raise

        # 優先嘗試以 export --format md 讀取 Google Doc
        res = self._run_gdrive(["readonly", "export", file_id, str(out_file), "--format", "md"])
        if res.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                return f.read()

        # 退回以 download 讀取普通檔案
        res_down = self._run_gdrive(["readonly", "download", file_id, "-o", str(out_file)])
        if res_down.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                return f.read()

        if listing_error:
            raise listing_error
        return None
