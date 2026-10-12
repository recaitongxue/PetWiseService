"""THU-Dogs 标注解析。

THU-Dogs 的每张图都有 head + body 两框（这是比 Stanford Dogs 多出的关键信息）。
训练时裁到 body 框能去掉背景噪声、显著提升品种分类准确率；
推理侧也可以借 bbox 做"先定位后识别"。

标注文件形如：

    <annotation>
      <filename>n100001.jpeg</filename>
      <size><width>720</width><height>720</height></size>
      <object>
        <name>Shiba_Dog</name>
        <headbndbox><xmin>..</xmin><ymin>..</ymin><xmax>..</xmax><ymax>..</ymax></headbndbox>
        <bodybndbox><xmin>..</xmin><ymin>..</ymin><xmax>..</xmax><ymax>..</ymax></bodybndbox>
      </object>
    </annotation>
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class BBox:
    xmin: int
    ymin: int
    xmax: int
    ymax: int

    @property
    def area(self) -> int:
        return max(0, self.xmax - self.xmin) * max(0, self.ymax - self.ymin)

    def scaled(self, sx: float, sy: float) -> "BBox":
        """把标注坐标系（xml 里的尺寸）映射到真实图片尺寸。"""
        return BBox(
            xmin=int(round(self.xmin * sx)),
            ymin=int(round(self.ymin * sy)),
            xmax=int(round(self.xmax * sx)),
            ymax=int(round(self.ymax * sy)),
        )

    def clipped(self, width: int, height: int) -> "BBox":
        return BBox(
            xmin=max(0, min(self.xmin, width)),
            ymin=max(0, min(self.ymin, height)),
            xmax=max(0, min(self.xmax, width)),
            ymax=max(0, min(self.ymax, height)),
        )


@dataclass(frozen=True)
class Annotation:
    filename: str
    size: tuple[int, int]                 # (width, height) 标注文件记录的尺寸
    head: BBox | None
    body: BBox | None


def _bbox(node: ET.Element | None) -> BBox | None:
    if node is None:
        return None
    try:
        return BBox(
            xmin=int(node.findtext("xmin", "0")),  # type: ignore[arg-type]
            ymin=int(node.findtext("ymin", "0")),  # type: ignore[arg-type]
            xmax=int(node.findtext("xmax", "0")),  # type: ignore[arg-type]
            ymax=int(node.findtext("ymax", "0")),  # type: ignore[arg-type]
        )
    except (TypeError, ValueError):
        return None


def parse_annotation(path: Path) -> Annotation:
    """解析单个标注 XML。缺失字段时返回 None，调用方需兜底。"""
    tree = ET.parse(path)
    root = tree.getroot()
    w = int(root.findtext("size/width", "0") or "0")
    h = int(root.findtext("size/height", "0") or "0")
    obj = root.find("object")
    if obj is None:
        return Annotation(filename=root.findtext("filename", ""), size=(w, h), head=None, body=None)
    return Annotation(
        filename=root.findtext("filename", "") or "",
        size=(w, h),
        head=_bbox(obj.find("headbndbox")),
        body=_bbox(obj.find("bodybndbox")),
    )


def parse_annotations(paths: Iterable[Path]) -> dict[str, Annotation]:
    """批量解析，key 为文件名（不含目录），便于按图检索。"""
    out: dict[str, Annotation] = {}
    for p in paths:
        try:
            ann = parse_annotation(p)
        except ET.ParseError:
            continue
        out[ann.filename] = ann
    return out
