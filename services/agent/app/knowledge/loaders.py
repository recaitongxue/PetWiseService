"""知识文档加载器。

支持的语料形态：
- Markdown（推荐，天然带标题结构）
- JSON / JSONL（适合从表格导出的问答对）
- CSV / TSV（FAQ 批量导入）

统一产出 CorpusDoc，让下游 pipeline 不需要关心文件类型。
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CorpusDoc:
    """加载到内存的原始语料。"""

    doc_id: str
    source_type: str
    title: str
    content: str
    species: str = "all"
    tags: list[str] = field(default_factory=list)
    source_uri: str = ""
    version: str = "v1"


_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_SUPPORTED_MARKDOWN = {".md", ".markdown", ".txt"}


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """解析 YAML 风格的 front matter。

    刻意不引入 PyYAML 依赖：语料元数据只需要简单的 key: value。
    """
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}, text

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("\"'")

    body = text[match.end() :]
    return meta, body


def _tags(meta: dict[str, str]) -> list[str]:
    raw = meta.get("tags", "")
    return [t.strip() for t in raw.split(",") if t.strip()]


def load_markdown(path: Path, *, default_source_type: str) -> CorpusDoc:
    meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
    # 一级标题作为文档标题，并从正文里去掉（它会被每个 chunk 的 heading 复用）
    first_heading = ""
    body_lines = body.strip().splitlines()
    if body_lines and body_lines[0].startswith("# "):
        first_heading = body_lines[0][2:].strip()
        body = "\n".join(body_lines[1:]).strip()

    return CorpusDoc(
        doc_id=meta.get("id") or path.stem,
        source_type=meta.get("source_type", default_source_type),
        title=meta.get("title") or first_heading or path.stem,
        content=body,
        species=meta.get("species", "all"),
        tags=_tags(meta),
        source_uri=str(path),
        version=meta.get("version", "v1"),
    )


def load_json(path: Path, *, default_source_type: str) -> list[CorpusDoc]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("items", [])
    docs: list[CorpusDoc] = []
    for i, row in enumerate(rows):
        docs.append(
            CorpusDoc(
                doc_id=str(row.get("id") or f"{path.stem}-{i}"),
                source_type=row.get("source_type", default_source_type),
                title=row.get("title") or row.get("question") or f"{path.stem}-{i}",
                content=row.get("content") or row.get("answer", ""),
                species=row.get("species", "all"),
                tags=row.get("tags", []),
                source_uri=str(path),
                version=row.get("version", "v1"),
            )
        )
    return docs


def load_csv(path: Path, *, default_source_type: str) -> list[CorpusDoc]:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    docs: list[CorpusDoc] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for i, row in enumerate(csv.DictReader(handle, delimiter=delimiter)):
            docs.append(
                CorpusDoc(
                    doc_id=row.get("id") or f"{path.stem}-{i}",
                    source_type=row.get("source_type", default_source_type),
                    title=row.get("title") or row.get("question") or f"{path.stem}-{i}",
                    content=row.get("content") or row.get("answer", ""),
                    species=row.get("species", "all"),
                    tags=[t for t in (row.get("tags") or "").split(",") if t],
                    source_uri=str(path),
                )
            )
    return docs


def _infer_source_type(path: Path, root: Path) -> str:
    """从目录结构推断来源类型：knowledge_base/diseases/xxx.md → disease。

    语料目录本身就是一套分类法，比在文件里再写一遍更不容易漂移。
    """
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "faq"
    if len(relative.parts) < 2:
        return "faq"
    folder = relative.parts[0]
    singular = folder[:-1] if folder.endswith("s") else folder
    return singular


def load_corpus(root: Path) -> list[CorpusDoc]:
    """递归加载整个语料目录。"""
    if not root.is_dir():
        raise FileNotFoundError(f"语料目录不存在: {root}")

    docs: list[CorpusDoc] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() in {".json", ".jsonl"}:
            docs.extend(load_json(path, default_source_type=_infer_source_type(path, root)))
        elif path.suffix.lower() in {".csv", ".tsv"}:
            docs.extend(load_csv(path, default_source_type=_infer_source_type(path, root)))
        elif path.suffix.lower() in _SUPPORTED_MARKDOWN:
            docs.append(load_markdown(path, default_source_type=_infer_source_type(path, root)))
    return docs
