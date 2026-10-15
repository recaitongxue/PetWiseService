"""THU-Dogs 标注解析与基于 bbox 的 letterbox 裁剪。

THU-Dogs 每张图提供两个 bbox：
  - headbndbox：头部框
  - bodybndbox：全身框
细粒度识别中，先裁剪到目标区域再resize，可显著抑制背景噪声、提升区分度
（与 "Fine-Grained Visual Classification" 系列方法中"先定位后识别"的思路一致）。

letterbox_crop 在裁剪后做**等比补边**（灰边），避免直接拉伸导致的几何畸变。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

Box = tuple[float, float, float, float]


def parse_annotation(xml_path: str | Path) -> dict[str, Box | None]:
    """解析 THU-Dogs 标注，返回 {"head": box, "body": box}，缺失为 None。"""
    try:
        tree = ET.parse(xml_path)
    except Exception:
        return {"head": None, "body": None}
    root = tree.getroot()
    out: dict[str, Box | None] = {"head": None, "body": None}
    for tag in ("headbndbox", "bodybndbox"):
        node = root.find(f".//{tag}")
        if node is None:
            continue
        try:
            xmin = float(node.find("xmin").text)  # type: ignore[union-attr]
            ymin = float(node.find("ymin").text)  # type: ignore[union-attr]
            xmax = float(node.find("xmax").text)  # type: ignore[union-attr]
            ymax = float(node.find("ymax").text)  # type: ignore[union-attr]
        except Exception:
            continue
        if xmax > xmin and ymax > ymin:
            out[tag[:4]] = (xmin, ymin, xmax, ymax)
    return out


def _union(a: Box, b: Box) -> Box:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def select_box(boxes: dict[str, Box | None], mode: str) -> Box | None:
    head = boxes.get("head")
    body = boxes.get("body")
    if mode == "head":
        return head
    if mode == "body":
        return body
    if mode == "union":
        if head and body:
            return _union(head, body)
        return head or body
    return None


def letterbox_crop(img: Image.Image, box: Box, fill: int = 128) -> Image.Image:
    """按 box 裁剪 img，并等比补边到正方形（边长=max(宽,高)），避免拉伸畸变。"""
    xmin, ymin, xmax, ymax = box
    # 限制在图像范围内
    w, h = img.size
    xmin = max(0.0, xmin)
    ymin = max(0.0, ymin)
    xmax = min(float(w), xmax)
    ymax = min(float(h), ymax)
    if xmax - xmin < 2 or ymax - ymin < 2:
        return img  # 退化情况直接返回原图
    crop = img.crop((int(xmin), int(ymin), int(xmax), int(ymax)))
    cw, ch = crop.size
    side = max(cw, ch)
    canvas = Image.new("RGB", (side, side), (fill, fill, fill))
    canvas.paste(crop, ((side - cw) // 2, (side - ch) // 2))
    return canvas


def load_bbox(breed_dir: str, img_name: str, ann_root: str | Path, mode: str) -> Box | None:
    """读取某张图的 bbox（按 mode 选择 head/body/union）。失败返回 None。"""
    if mode in ("none", ""):
        return None
    ann_root = Path(ann_root)
    # 标注文件名 = 图片文件名 + ".xml"
    xml_name = img_name if img_name.endswith(".xml") else img_name + ".xml"
    xml_path = ann_root / breed_dir / xml_name
    if not xml_path.exists():
        return None
    boxes = parse_annotation(xml_path)
    return select_box(boxes, mode)
