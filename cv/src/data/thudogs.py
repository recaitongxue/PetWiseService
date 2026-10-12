"""THU-Dogs 数据集（torch 相关）。

纯解析与类别映射见 thudogs_meta.py（可无 GPU 验证）。
数据集布局（cv/datasets/）：
    high-resolution/<BREED>/<img>.(jpeg|jpg)
    high-annotations/<BREED>/<img>.(jpeg|jpg).xml   # head/body bbox
    TrainAndValList/train.lst / validation.lst

设计要点
--------
1. split 直接由官方 lst 决定，不再随机划分（可复现、可答辩）。
2. 列表里写 `.jpeg`，磁盘上可能是 `.jpg`，resolve 时两种都试（见 thudogs_meta）。
3. 训练默认裁到 body 框：去背景、提精度；缺框则退回整图。
4. 类别下标由"按文件夹名排序"唯一确定，与 labels.json 下标严格一致。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from collections import Counter
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.transforms import InterpolationMode

from src.data.annotation import Annotation, parse_annotation
from src.data.thudogs_meta import (
    _NORM_MEAN,
    _NORM_STD,
    build_class_map,
    clean_lines,
    make_labels,
    resolve_image_path,
)


# ── 变换 ────────────────────────────────────────────────────
def build_transforms(image_size: int = 224, *, train: bool = True) -> transforms.Compose:
    if train:
        return transforms.Compose(
            [
                transforms.RandomResizedCrop(image_size, scale=(0.85, 1.0)),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(0.2, 0.2, 0.15, 0.05),
                transforms.ToTensor(),
                transforms.Normalize(_NORM_MEAN, _NORM_STD),
            ]
        )
    return transforms.Compose(
        [
            # 必须与 services/vision/app/preprocess.py 的 to_tensor 一致：
            # ImageOps.fit 等价于「短边缩放到 image_size(双三次) + 中心裁剪」，
            # 否则离线 val 与线上推理预处理不同，精度会无声下降。
            transforms.Resize(image_size, interpolation=InterpolationMode.BICUBIC),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(_NORM_MEAN, _NORM_STD),
        ]
    )


@dataclass
class _Sample:
    image: Path
    annotation: Path | None
    label: int


class THUDogsDataset(Dataset):
    def __init__(
        self,
        root: Path,
        *,
        split: str = "train",
        image_size: int = 224,
        use_bbox: bool = True,
        train: bool = True,
        classes: list[str] | None = None,
        class_to_idx: dict[str, int] | None = None,
    ) -> None:
        self.root = Path(root)
        self.images_dir = self.root / "high-resolution"
        self.ann_dir = self.root / "high-annotations"
        self.image_size = image_size
        self.use_bbox = use_bbox
        self.transform = build_transforms(image_size, train=train)

        list_file = self.root / "TrainAndValList" / f"{split}.lst"
        if not list_file.is_file():
            raise FileNotFoundError(f"找不到划分文件: {list_file}")

        # 优先用外部传入的共享类映射（train/val 下标强一致、支持白名单）；
        # 单独实例化时才从自身 lst 推导（保持向后兼容）。
        if class_to_idx is not None and classes is not None:
            self.classes = classes
            self.class_to_idx = class_to_idx
        else:
            self.classes, self.class_to_idx = build_class_map([list_file])

        self.samples: list[_Sample] = []
        skipped = 0
        for rel in clean_lines(list_file):
            breed = Path(rel).parent.name
            if breed not in self.class_to_idx:  # 白名单过滤：跳过不在训练集的品种
                skipped += 1
                continue
            img = resolve_image_path(self.images_dir, rel)
            if img is None:
                skipped += 1
                continue
            ann: Path | None = self.ann_dir / f"{rel}.xml" if self.ann_dir.is_dir() else None
            if ann is not None and not ann.is_file():
                ann = None
            self.samples.append(_Sample(img, ann, class_to_idx[breed]))

        if skipped:
            print(f"[thudogs] {split}: 跳过 {skipped} 张无法定位的图片（扩展名不匹配等）")
        if not self.samples:
            raise ValueError(f"{split} 未解析到任何图片，请检查数据集路径")

    def __len__(self) -> int:
        return len(self.samples)

    def _crop_box(self, image: Image.Image, ann: Annotation) -> Image.Image:
        if not self.use_bbox:
            return image
        box = ann.body or ann.head
        if box is None:
            return image
        w, h = image.size
        aw, ah = ann.size
        sx = (w / aw) if aw else 1.0
        sy = (h / ah) if ah else 1.0
        b = box.scaled(sx, sy).clipped(w, h)
        if b.area < 64:  # 框太小直接放弃
            return image
        pad_x, pad_y = int((b.xmax - b.xmin) * 0.04), int((b.ymax - b.ymin) * 0.04)
        return image.crop(
            (max(0, b.xmin - pad_x), max(0, b.ymin - pad_y), b.xmax + pad_x, b.ymax + pad_y)
        )

    def __getitem__(self, index: int):
        # 容错：遇到损坏图片自动跳到下一张，避免一次坏图中断整轮
        for attempt in range(index, min(index + 8, len(self.samples))):
            sample = self.samples[attempt]
            try:
                image = Image.open(sample.image).convert("RGB")
                if sample.annotation is not None:
                    image = self._crop_box(image, parse_annotation(sample.annotation))
                return self.transform(image), sample.label
            except Exception:  # noqa: BLE001 - 单图异常不致命
                continue
        placeholder = Image.new("RGB", (self.image_size, self.image_size), (128, 128, 128))
        return self.transform(placeholder), self.samples[index].label


def build_loaders(
    root: Path,
    *,
    image_size: int = 224,
    batch_size: int = 32,
    num_workers: int = 4,
    use_bbox: bool = True,
    balanced: bool = True,
    whitelist: list[str] | None = None,
    seed: int = 42,
    test_split: bool = True,
) -> tuple[DataLoader, DataLoader, DataLoader | None, list[str]]:
    """构造 train / val / test 的 DataLoader 与类别名列表。

    - 类映射统一由 train + (val|validation) + test 合并推导，三路下标强一致；
    - val 优先用切分出的 val.lst（prepare 阶段生成），否则退回官方 validation.lst；
    - test_split=True 且 test.lst 存在时额外返回 test_loader；否则为 None（评测退回 val）；
    - balanced=True 时按类频反比加权采样，抵消长尾（头部 7409 张 vs 尾部 160 张）；
    - seed 固定后，加权采样与切分都可在其他机器上复现。
    """
    root = Path(root)
    tlist = root / "TrainAndValList"
    val_lst = tlist / "val.lst"
    test_lst = tlist / "test.lst"

    # 合并类映射：train + val（切分优先）+ test（若存在），杜绝分 split 推导的下标错位
    map_files = [tlist / "train.lst"]
    map_files.append(val_lst if val_lst.is_file() else tlist / "validation.lst")
    if test_split and test_lst.is_file():
        map_files.append(test_lst)
    classes, class_to_idx = build_class_map(map_files, whitelist=whitelist)

    val_split_name = "val" if val_lst.is_file() else "validation"
    train_set = THUDogsDataset(
        root, split="train", image_size=image_size, use_bbox=use_bbox,
        train=True, classes=classes, class_to_idx=class_to_idx,
    )
    val_set = THUDogsDataset(
        root, split=val_split_name, image_size=image_size, use_bbox=use_bbox,
        train=False, classes=classes, class_to_idx=class_to_idx,
    )

    train_loader = DataLoader(
        train_set, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True
    )
    if balanced:
        targets = [s.label for s in train_set.samples]
        counts = Counter(targets)
        # 每类每轮被抽中的期望次数相同（按 1/类样本数 加权）
        sample_weights = [len(targets) / counts[t] for t in targets]
        sampler = WeightedRandomSampler(
            sample_weights, num_samples=len(targets), replacement=True,
            generator=torch.Generator().manual_seed(seed),
        )
        train_loader = DataLoader(
            train_set, batch_size=batch_size, sampler=sampler,
            num_workers=num_workers, pin_memory=True,
        )
    val_loader = DataLoader(
        val_set, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True
    )

    test_loader: DataLoader | None = None
    if test_split and test_lst.is_file():
        test_set = THUDogsDataset(
            root, split="test", image_size=image_size, use_bbox=use_bbox,
            train=False, classes=classes, class_to_idx=class_to_idx,
        )
        test_loader = DataLoader(
            test_set, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True
        )
    return train_loader, val_loader, test_loader, classes
