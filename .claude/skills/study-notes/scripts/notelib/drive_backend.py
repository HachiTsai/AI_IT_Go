"""gdrive CLI 後端：只有真的要進 Google Drive 時才會被匯入。"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import StorageBackend
from .common import format_note, note_stem, sanitize_filename

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

    def _get_or_create_repo_folder(self, repo: str) -> str:
        res = self._run_gdrive(["readonly", "ls", self.folder_id, "--json"])
        if res.returncode == 0:
            try:
                items = json.loads(res.stdout.strip() or "[]")
                for item in items:
                    if item.get("name") == repo and item.get("mimeType") == "application/vnd.google-apps.folder":
                        return item["id"]
            except Exception:
                pass

        res_mkdir = self._run_gdrive(["mutate", "mkdir", repo, "--parent", self.folder_id, "--json"])
        if res_mkdir.returncode == 0:
            try:
                data = json.loads(res_mkdir.stdout.strip())
                if "id" in data:
                    return data["id"]
            except Exception:
                pass
        return self.folder_id

    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
    ) -> Tuple[str, str]:
        repo_folder_id = self._get_or_create_repo_folder(repo)
        clean_title = note_stem(category, title)

        clean_ext = ".csv" if doc_format == "sheet" else ".md"
        temp_name = f"{clean_title}{clean_ext}"

        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / temp_name

        formatted = format_note(repo, category, title, content, tags)
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(formatted)

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
            return (
                f"上傳 Google Drive 失敗：{res.stderr.strip()}",
                str(temp_file),
            )

        # 從回傳中提取 File ID
        m = re.search(r"\(ID:\s*([^\)]+)\)", res.stdout)
        file_id = m.group(1) if m else ""

        if not file_id:
            try:
                data = json.loads(res.stdout.strip())
                file_id = data.get("id", "")
            except Exception:
                pass

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

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        notes = []
        if repo:
            target_folders = [(repo, self._get_or_create_repo_folder(repo))]
        else:
            # 遍歷所有 repo 資料夾以列出真正的筆記文件
            target_folders = []
            res_root = self._run_gdrive(["readonly", "ls", self.folder_id, "--json"])
            if res_root.returncode == 0:
                try:
                    for item in json.loads(res_root.stdout.strip() or "[]"):
                        if item.get("mimeType") == "application/vnd.google-apps.folder":
                            target_folders.append((item.get("name"), item.get("id")))
                except Exception:
                    pass

        for r_name, f_id in target_folders:
            res = self._run_gdrive(["readonly", "ls", f_id, "--json"])
            if res.returncode == 0:
                try:
                    items = json.loads(res.stdout.strip() or "[]")
                    for item in items:
                        mime = item.get("mimeType", "")
                        if mime == "application/vnd.google-apps.folder":
                            continue
                        if mime in WORKSPACE_TYPE_NAMES or item.get("name", "").endswith(".md"):
                            type_name = WORKSPACE_TYPE_NAMES.get(mime, "Markdown 📝")
                            notes.append(
                                {
                                    "repo": r_name,
                                    "filename": item.get("name"),
                                    "type": type_name,
                                    "id": item.get("id"),
                                    "modified": item.get("modifiedTime", ""),
                                }
                            )
                except Exception:
                    pass
        notes.sort(key=lambda x: (x["repo"], x["filename"]))
        return notes

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        res = self._run_gdrive(["readonly", "search", "--name-contains", query, "--json"])
        results = []
        if res.returncode == 0:
            try:
                items = json.loads(res.stdout.strip() or "[]")
                for item in items:
                    mime = item.get("mimeType", "")
                    type_name = WORKSPACE_TYPE_NAMES.get(mime, "檔案")
                    results.append(
                        {
                            "repo": repo or "Remote",
                            "filename": item.get("name"),
                            "type": type_name,
                            "id": item.get("id"),
                            "snippet": f"匹配 Drive {type_name}: {item.get('name')}",
                        }
                    )
            except Exception:
                pass
        return results

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        out_file = temp_dir / "read_note.md"

        file_id = identifier

        # 優先從清單中依檔名或 ID 比對
        matched_id = None
        all_notes = self.list_notes(repo)

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
            file_id = matched_id

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

        return None
