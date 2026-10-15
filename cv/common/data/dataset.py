"""数据集定义：THU-Dogs（狗）与 ImageFolder（猫）两套，统一由 build_dataset 分发。"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset

from . import bbox as bbox_mod
from .labels import load_labels


class THUDogsDataset(Dataset):
    """THU-Dogs 数据集：按 TrainAndValList/<split>.lst 读取样本。

    lst 行格式：`.//1043-n000001-Shiba_Dog/n100001.jpeg`
    类别由首级目录（品种目录）决定，索引来自 labels-<kind>.json。
    """

    def __init__(
        self,
        image_root: str | Path,
        split_file: str | Path,
        folder_to_idx: dict[str, int],
        transform=None,
        use_bbox: bool = False,
        bbox_mode: str = "body",
        ann_root: str | Path | None = None,
    ):
        self.image_root = Path(image_root)
        self.transform = transform
        self.use_bbox = use_bbox
        self.bbox_mode = bbox_mode
        self.ann_root = Path(ann_root) if ann_root else None
        self._bbox_cache: dict[tuple[str, str], tuple | None] = {}

        self.samples: list[tuple[str, int]] = []
        with open(split_file, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rel = line.lstrip("./\\").replace("\\", "/")
                parts = rel.split("/")
                if len(parts) < 2:
                    continue
                breed, img = parts[0], parts[1]
                if breed not in folder_to_idx:
                    continue
                self.samples.append((str(self.image_root / rel), folder_to_idx[breed]))

    def __len__(self) -> int:
        return len(self.samples)

    def _get_bbox(self, breed: str, img_name: str):
        key = (breed, img_name)
        if key in self._bbox_cache:
            return self._bbox_cache[key]
        box = None
        if self.use_bbox and self.ann_root is not None:
            box = bbox_mod.load_bbox(breed, img_name, self.ann_root, self.bbox_mode)
        self._bbox_cache[key] = box
        return box

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.use_bbox and self.ann_root is not None:
            breed = Path(path).parent.name
            img_name = Path(path).name
            box = self._get_bbox(breed, img_name)
            if box is not None:
                img = bbox_mod.letterbox_crop(img, box)
        if self.transform is not None:
            img = self.transform(img)
        return img, label


class ImageFolderDataset(Dataset):
    """标准 ImageFolder（猫）：root/<split>/<class>/*。"""

    def __init__(self, root: str | Path, class_to_idx: dict[str, int], transform=None):
        self.root = Path(root)
        self.transform = transform
        self.samples: list[tuple[str, int]] = []
        for cls in sorted(class_to_idx):
            d = self.root / cls
            if not d.is_dir():
                continue
            for p in d.iterdir():
                if p.is_file():
                    self.samples.append((str(p), class_to_idx[cls]))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform is not None:
            img = self.transform(img)
        return img, label


def build_dataset(
    kind: str,
    split: str,
    cfg: dict,
    artifacts_dir: str | Path,
    transform=None,
) -> Dataset:
    """按 kind 与 dataset.yaml 构建对应 Dataset。"""
    labels = load_labels(kind, artifacts_dir)
    folder_to_idx = labels["folder_to_idx"]
    ds = cfg["dataset"]
    if kind == "dog":
        split_file = Path(ds["split_dir"]) / ds["splits"][split]
        return THUDogsDataset(
            image_root=ds["image_root"],
            split_file=split_file,
            folder_to_idx=folder_to_idx,
            transform=transform,
            use_bbox=bool(ds.get("use_bbox", False)),
            bbox_mode=ds.get("bbox_mode", "body"),
            ann_root=ds.get("annotations_root"),
        )
    elif kind == "cat":
        root = Path(ds["image_root"]) / split
        return ImageFolderDataset(
            root=root, class_to_idx=folder_to_idx, transform=transform
        )
    raise ValueError(f"未知 kind={kind}")
