"""文本切分策略。

默认走「标题感知」：先按 Markdown 标题切开，再对超长段落做二次滑窗。
为什么不能直接按固定长度切：知识条目里一个症状段落被切断，
检索召回的会是半句话，LLM 也就不可能引用到正确来源。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import settings

_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


@dataclass
class Chunk:
    """切分后的片段，尚未落库。"""

    index: int
    heading: str
    content: str

    @property
    def token_count(self) -> int:
        """粗估 token 数：中文按字符、英文按 4 字符一个 token。"""
        chinese = len(re.findall(r"[\u4e00-\u9fff]", self.content))
        others = len(self.content) - chinese
        return chinese + max(1, others // 4)

    @property
    def embed_text(self) -> str:
        """送进 embedding 的文本：带上标题能显著提升召回质量。"""
        return f"{self.heading}\n{self.content}" if self.heading else self.content


def split_markdown(document: str) -> list[tuple[str, str]]:
    """按标题把 Markdown 拆成 [(heading, body)]。

    实现要点：先单独处理「第一个标题之前」的导言，
    再统一按「标题 → 下一个标题」取正文。
    写成两次独立的收集会产生重复片段。
    """
    matches = list(_HEADING_PATTERN.finditer(document))
    if not matches:
        return [("", document.strip())]

    sections: list[tuple[str, str]] = []

    preamble = document[: matches[0].start()].strip()
    if preamble:
        sections.append(("", preamble))

    positions = [(m.start(), m.group(2).strip()) for m in matches]
    positions.append((len(document), ""))
    for i in range(len(positions) - 1):
        start, heading = positions[i]
        end = positions[i + 1][0]
        # 去掉该段起始处的标题行，只保留正文
        body = _HEADING_PATTERN.sub("", document[start:end]).strip()
        if body:
            sections.append((heading, body))

    return sections or [("", document.strip())]


def _sliding(text: str, size: int, overlap: int) -> list[str]:
    """二次滑窗切分，保留 overlap 保证语义跨窗连续。"""
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    step = max(1, size - overlap)
    start = 0
    while start < len(text):
        piece = text[start : start + size]
        chunks.append(piece)
        if start + size >= len(text):
            break
        start += step
    return chunks


def chunk_text(
    document: str,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """标题优先 + 滑窗兜底的混合切分。"""
    size = chunk_size or settings.CHUNK_SIZE
    window_overlap = overlap or settings.CHUNK_OVERLAP

    pieces: list[Chunk] = []
    index = 0
    for heading, body in split_markdown(document):
        # 优先按空行再切一层，避免把多个要点揉在一起
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) + 1 <= size:
                buffer = f"{buffer}\n\n{paragraph}".strip()
                continue
            if buffer:
                for piece in _sliding(buffer, size, window_overlap):
                    pieces.append(Chunk(index=index, heading=heading, content=piece))
                    index += 1
            buffer = paragraph
        if buffer:
            for piece in _sliding(buffer, size, window_overlap):
                pieces.append(Chunk(index=index, heading=heading, content=piece))
                index += 1

    if not pieces:  # 极短文档兜底
        pieces = [Chunk(index=0, heading="", content=document.strip()[:size])]

    return pieces
