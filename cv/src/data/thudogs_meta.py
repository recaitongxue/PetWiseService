"""THU-Dogs 元数据工具（不依赖 torch，可在纯 CPU 环境验证）。

包含：lst 解析、扩展名容错、文件夹名→品种、类别映射、labels.json 生成。
torch 相关（Dataset / transforms）在 thudogs.py，本文件保持零重依赖，方便单测。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# 与 services/vision 的归一化保持一致
_NORM_MEAN = [0.485, 0.456, 0.406]
_NORM_STD = [0.229, 0.224, 0.225]

_IMG_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
_FOLDER_RE = re.compile(r"^(?P<id>\d+)-(?P<code>n\d+)-(?P<name>.+)$")


def clean_lines(path: Path) -> list[str]:
    """读 lst，去掉 BOM / \\r / 空行，并把 `.//` 前缀规一成 `BREED/IMG`。"""
    text = Path(path).read_text(encoding="utf-8-sig")
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip().lstrip(".").lstrip("/").strip()
        if line:
            out.append(line)
    return out


def resolve_image_path(images_dir: Path, rel: str) -> Path | None:
    """按 lst 里的相对路径定位真实图片，容忍 .jpeg / .jpg 扩展名差异。"""
    images_dir = Path(images_dir)
    base = images_dir / rel
    if base.is_file():
        return base
    for alt in (".jpeg", ".jpg", ".png"):
        candidate = base.with_suffix(alt)
        if candidate.is_file():
            return candidate
    for f in base.parent.glob(f"{base.stem}.*"):
        if f.suffix.lower() in _IMG_SUFFIXES:
            return f
    return None


def parse_folder_name(folder: str) -> tuple[str, str]:
    """`1043-n000001-Shiba_Dog` -> ('n000001', 'Shiba Dog')。"""
    m = _FOLDER_RE.match(folder)
    if not m:
        return folder, folder.replace("_", " ")
    return m.group("code"), m.group("name").replace("_", " ")


def build_class_map(
    list_files: Iterable[Path], *, whitelist: Iterable[str] | None = None
) -> tuple[list[str], dict[str, int]]:
    """从官方 lst 收集全部品种（按文件夹名排序），返回 (classes, class_to_idx)。

    whitelist 非空时只保留列表内的品种文件夹名——用于 MVP 只训头部常见犬。
    无论传几个 lst，返回的排序结果都确定，保证 train/val/labels 下标强一致。
    """
    breeds: set[str] = set()
    for lf in list_files:
        for rel in clean_lines(Path(lf)):
            breed = Path(rel).parent.name
            if breed:
                breeds.add(breed)
    if whitelist is not None:
        wanted = set(whitelist)
        breeds = {b for b in breeds if b in wanted}
    classes = sorted(breeds)
    return classes, {name: i for i, name in enumerate(classes)}


def make_labels(
    root: Path,
    *,
    out_path: Path,
    version: str = "v1",
    image_size: int = 224,
    cn_map: dict[str, str] | None = None,
    whitelist: Iterable[str] | None = None,
) -> list[dict]:
    """生成 labels.json：下标即模型输出的类 id，结构与 services/vision 的 Labels 对齐。

    whitelist 与训练侧 build_loaders 共用，保证 labels 下标 = 推理类 id。
    """
    root = Path(root)
    tlist = root / "TrainAndValList"
    val_lst = tlist / "val.lst"
    test_lst = tlist / "test.lst"
    lists = [tlist / "train.lst"]
    lists.append(val_lst if val_lst.is_file() else tlist / "validation.lst")
    # 切分出测试集后，标签表也要覆盖 test，保证 labels 下标 = 推理类 id
    if test_lst.is_file():
        lists.append(test_lst)
    classes, _ = build_class_map(lists, whitelist=whitelist)

    labels: list[dict] = []
    for folder in classes:
        code, en = parse_folder_name(folder)
        cn = (cn_map or {}).get(code) or (cn_map or {}).get(en.lower()) or en
        labels.append(
            {
                "breedId": f"dog-{code}",
                "title": cn,
                "nameEn": en,
                "sci": "Canis lupus familiaris",
                "species": "dog",
            }
        )

    payload = {
        "kind": "dog",
        "version": version,
        "imageSize": image_size,
        "mean": _NORM_MEAN,
        "std": _NORM_STD,
        "numClasses": len(labels),
        "labels": labels,
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return labels
