"""本機 Markdown 後端：不需任何雲端依賴，是 gdrive CLI 不在時的退路。"""

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import StorageBackend
from .common import ensure_folder_allowed, format_note, is_no_open, note_stem, sanitize_filename


class LocalStorageBackend(StorageBackend):
    def __init__(self, root_dir: Path):
        for part in root_dir.resolve().parts:
            ensure_folder_allowed(part)
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

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
        ensure_folder_allowed(repo)
        repo_dir = self.root_dir / sanitize_filename(repo)
        repo_dir.mkdir(parents=True, exist_ok=True)

        clean_title = note_stem(category, title)

        filename = f"{clean_title}.md"
        target_path = repo_dir / filename
        formatted_content = format_note(repo, category, title, content, tags)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        return (
            f"成功寫入本機筆記備份: {filename}",
            str(target_path),
        )

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        notes = []
        if repo:
            ensure_folder_allowed(repo)
            target_dirs = [self.root_dir / sanitize_filename(repo)]
        else:
            target_dirs = [p for p in self.root_dir.iterdir() if not is_no_open(p.name) and p.is_dir()]
        # 捷徑或符號連結指向 no open 資料夾也不進入
        target_dirs = [p for p in target_dirs if not any(is_no_open(part) for part in p.resolve().parts)]

        for r_dir in target_dirs:
            if not r_dir.exists():
                continue
            for file_path in r_dir.glob("*.md"):
                try:
                    stat = file_path.stat()
                    notes.append(
                        {
                            "repo": r_dir.name,
                            "filename": file_path.name,
                            "type": "Markdown 📝",
                            "path": str(file_path),
                            "modified": datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                except Exception:
                    pass
        notes.sort(key=lambda x: (x["repo"], x["filename"]))
        return notes

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        all_notes = self.list_notes(repo)
        query_lower = query.lower()
        results = []

        for note in all_notes:
            file_path = Path(note["path"])
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                matched = False
                snippet = ""
                if query_lower in note["filename"].lower():
                    matched = True
                    snippet = "匹配檔名"
                elif query_lower in content.lower():
                    matched = True
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 40)
                    end = min(len(content), idx + 60)
                    snippet = "..." + content[start:end].replace("\n", " ") + "..."

                if matched:
                    res = dict(note)
                    res["snippet"] = snippet
                    results.append(res)
            except Exception:
                continue

        return results

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        if repo:
            ensure_folder_allowed(repo)
        target = Path(identifier)
        if target.exists() and target.is_file():
            for part in target.resolve().parts[:-1]:
                ensure_folder_allowed(part)
            with open(target, "r", encoding="utf-8") as f:
                return f.read()

        all_notes = self.list_notes(repo)
        for note in all_notes:
            if (
                note["filename"] == identifier
                or note["filename"].lower() == identifier.lower()
                or identifier.lower() in note["filename"].lower()
            ):
                with open(note["path"], "r", encoding="utf-8") as f:
                    return f.read()
        return None
