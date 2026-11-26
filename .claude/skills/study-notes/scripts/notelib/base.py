"""儲存後端介面。"""

from typing import Dict, List, Optional, Tuple


class StorageBackend:
    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
    ) -> Tuple[str, str]:
        """新增筆記，回傳 (狀態訊息, 檔案路徑或ID或URL)"""
        raise NotImplementedError

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        """檢索筆記"""
        raise NotImplementedError

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        """讀取筆記內容"""
        raise NotImplementedError

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        """列出筆記"""
        raise NotImplementedError
