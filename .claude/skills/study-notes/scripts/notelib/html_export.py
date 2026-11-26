"""Markdown → HTML：讓內嵌圖片的筆記能以 text/html 上傳並由 Google Drive 轉成 Google 文件。

Google Drive 匯入 Markdown 時圖片只能用外部網址；改傳 HTML 時 base64 內嵌圖片會被保留（2026-11-26 實測）。
"""

import html
import re

import markdown as md_lib

_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n+", re.S)


def strip_frontmatter(text: str) -> str:
    return _FRONTMATTER.sub("", text, count=1)


def markdown_to_html(text: str, title: str) -> str:
    """轉成完整 HTML 文件。frontmatter 不放進內文，原始 HTML（例如內嵌 <img>）原樣保留。"""
    body = md_lib.markdown(strip_frontmatter(text), extensions=["tables", "fenced_code", "sane_lists"])
    return (
        '<html><head><meta charset="utf-8"><title>'
        + html.escape(title)
        + "</title></head><body>"
        + body
        + "</body></html>"
    )
