"""Mermaid 支援：擷取 ```mermaid 區塊、基本檢查、（選用）用 mermaid-cli 轉圖。

設計原則：
- 預設保留原始 ```mermaid 區塊不動。2026-11-26 實測：Google 文件匯入 Markdown 後，區塊變成
  原生程式碼區塊（語言標籤「None」，清單沒有 Mermaid），不會渲染成圖；用 `read` 匯出 md 時
  原始碼完整，但 mermaid 標籤會丟失，只剩無語言的 ```。
- 檢查只做「肯定錯」的判斷（圍欄未閉合、第一行不是已知圖表類型、空區塊），
  不嘗試完整解析 Mermaid 語法，避免誤報。
- 轉圖是選用功能，需自行安裝 mermaid-cli（mmdc）；沒有時明確回報而不是靜默略過。
"""

import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Mermaid 目前常見的圖表宣告關鍵字（第一個有效行必須以其中之一開頭）
DIAGRAM_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "stateDiagram-v2", "erDiagram", "journey", "gantt", "pie", "quadrantChart",
    "requirementDiagram", "gitGraph", "mindmap", "timeline", "zenuml", "sankey",
    "sankey-beta", "xychart", "xychart-beta", "block", "block-beta", "packet",
    "packet-beta", "architecture", "architecture-beta", "kanban", "C4Context",
    "C4Container", "C4Component", "C4Dynamic", "C4Deployment", "radar", "radar-beta",
)

_FENCE_OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[\w+#.-]*)[ \t]*$", re.I)


@dataclass
class MermaidBlock:
    index: int  # 第幾個 mermaid 區塊（從 1 起算）
    start_line: int  # 開圍欄所在行（從 1 起算）
    code: str
    closed: bool = True
    end_line: int = 0  # 結尾圍欄所在行（未閉合時為最後一行），從 1 起算
    issues: List[str] = field(default_factory=list)


def extract_blocks(markdown: str) -> List[MermaidBlock]:
    """依序擷取所有 ```mermaid 區塊（含未閉合者）。

    也會認出「沒有語言標籤、但內容第一行是已知圖表宣告」的圍欄：Google 文件匯入 Markdown 後，
    ```mermaid 會變成原生程式碼區塊並丟失 mermaid 標籤，匯出時只剩 ```。
    """
    lines = markdown.splitlines()
    blocks: List[MermaidBlock] = []
    i = 0
    while i < len(lines):
        m = _FENCE_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        fence_char = m.group("fence")[0]
        fence_len = len(m.group("fence"))
        close_re = re.compile(rf"^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$")
        start = i
        body: List[str] = []
        i += 1
        closed = False
        end_line = start + 1
        while i < len(lines):
            end_line = i + 1
            if close_re.match(lines[i]):
                closed = True
                i += 1
                break
            body.append(lines[i])
            i += 1
        lang = m.group("lang").lower()
        if lang not in ("", "mermaid"):
            continue  # 其他語言的圍欄整段略過，避免把它的結尾圍欄誤當成新的開頭
        code = "\n".join(body).strip("\n")
        if not lang:
            first = _first_meaningful_line(code)
            if not (closed and first and _is_diagram_decl(first)):
                continue
        blocks.append(
            MermaidBlock(index=len(blocks) + 1, start_line=start + 1, code=code, closed=closed, end_line=end_line)
        )
    return blocks


def _first_meaningful_line(code: str) -> Optional[str]:
    in_frontmatter = False
    for n, raw in enumerate(code.splitlines()):
        line = raw.strip()
        if n == 0 and line == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line == "---":
                in_frontmatter = False
            continue
        if not line or line.startswith("%%"):
            continue
        return line
    return None


def _is_diagram_decl(line: str) -> bool:
    return any(line == t or line.startswith(t + " ") or line.startswith(t + "\t") for t in DIAGRAM_TYPES)


def validate_block(block: MermaidBlock) -> MermaidBlock:
    """檢查單一區塊，問題寫入 block.issues 並回傳同一物件。"""
    block.issues = []
    if not block.closed:
        block.issues.append("圍欄沒有閉合（缺少結尾的 ```）")
    if not block.code.strip():
        block.issues.append("區塊是空的")
        return block
    first = _first_meaningful_line(block.code)
    if first is None:
        block.issues.append("只有註解，沒有圖表內容")
    elif not _is_diagram_decl(first):
        block.issues.append(f"第一行 '{first[:40]}' 不是已知的 Mermaid 圖表宣告（例如 flowchart TD、sequenceDiagram）")
    if block.code.count("[") != block.code.count("]") or block.code.count("(") != block.code.count(")"):
        block.issues.append("括號數量不成對，可能有節點文字沒閉合")
    return block


def check_markdown(markdown: str) -> List[MermaidBlock]:
    """擷取並檢查全部區塊。"""
    return [validate_block(b) for b in extract_blocks(markdown)]


def find_mmdc() -> Optional[str]:
    """尋找 mermaid-cli（mmdc）。可用環境變數 MMDC_BIN 指定路徑。"""
    env_bin = os.environ.get("MMDC_BIN")
    if env_bin and os.access(env_bin, os.X_OK):
        return env_bin
    return shutil.which("mmdc")


def _puppeteer_config_file() -> Optional[str]:
    """容器內常需指定 Chromium 並關閉沙箱；有 MERMAID_CHROME_PATH 或預裝 Chromium 時產生設定檔。"""
    chrome = os.environ.get("MERMAID_CHROME_PATH") or (
        "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    )
    if not chrome:
        return None
    cfg = {"executablePath": chrome, "args": ["--no-sandbox", "--headless"]}
    fd, path = tempfile.mkstemp(suffix=".json", prefix="mmdc-puppeteer-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return path


def png_size(path: Path) -> Tuple[int, int]:
    """讀 PNG 檔頭取得 (寬, 高) 像素。"""
    header = Path(path).read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"不是 PNG 檔：{path}")
    return struct.unpack(">II", header[16:24])


def render_blocks(markdown: str, out_dir: Path, fmt: str = "png") -> List[Path]:
    """用 mmdc 把每個通過檢查的區塊轉成圖檔，回傳產生的檔案。

    找不到 mmdc 時丟 RuntimeError，由呼叫端決定如何呈現。
    """
    mmdc = find_mmdc()
    if not mmdc:
        raise RuntimeError("找不到 mermaid-cli（mmdc）。請先安裝：npm install -g @mermaid-js/mermaid-cli")
    out_dir.mkdir(parents=True, exist_ok=True)
    pp_config = _puppeteer_config_file()
    produced: List[Path] = []
    for block in check_markdown(markdown):
        if block.issues:
            raise ValueError(f"Mermaid 區塊 #{block.index}（第 {block.start_line} 行）有問題：" + "；".join(block.issues))
        src = out_dir / f"diagram-{block.index}.mmd"
        dst = out_dir / f"diagram-{block.index}.{fmt}"
        src.write_text(block.code + "\n", encoding="utf-8")
        cmd = [mmdc, "-i", str(src), "-o", str(dst), "-b", "white"]
        if fmt == "png":
            cmd += ["-s", "2"]
        if pp_config:
            cmd += ["-p", pp_config]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"mmdc 轉圖失敗（區塊 #{block.index}）：{res.stderr.strip()[:300]}")
        produced.append(dst)
    return produced


def embed_images(markdown: str, out_dir: Path, max_width: int = 620, max_height: int = 700) -> str:
    """把每個 mermaid 區塊轉成 PNG 並換成內嵌 base64 的 HTML <img>，其餘內容不動。

    回傳的文字交給 Markdown→HTML 轉換（原始 HTML 會被保留）。圖依 PNG 尺寸（2 倍縮放）換算顯示大小，
    不超過 max_width × max_height，避免直式流程圖佔滿整頁。
    """
    import base64

    blocks = check_markdown(markdown)
    if not blocks:
        return markdown
    pngs: Dict[int, Path] = {b.index: p for b, p in zip(blocks, render_blocks(markdown, out_dir, fmt="png"))}
    lines = markdown.splitlines()
    # 由後往前替換，行號才不會位移
    for block in reversed(blocks):
        start, end = block.start_line - 1, block.end_line
        png = pngs[block.index]
        w, h = png_size(png)
        w, h = w / 2, h / 2
        scale = min(1.0, max_width / w, max_height / h)
        data = base64.b64encode(png.read_bytes()).decode("ascii")
        img = (
            f'<p><img src="data:image/png;base64,{data}" width="{int(w * scale)}" height="{int(h * scale)}" '
            f'alt="Mermaid 圖 {block.index}"></p>'
        )
        lines[start:end] = [img]
    return "\n".join(lines) + "\n"
