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
        html: Optional[str] = None,
    ) -> Tuple[str, str]:
        """新增筆記，回傳 (狀態訊息, 檔案路徑或ID或URL)。

        html：已含內嵌圖片的完整 HTML；只有 Drive 後端會用它上傳並轉成 Google 文件，其他後端忽略。
        """
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
