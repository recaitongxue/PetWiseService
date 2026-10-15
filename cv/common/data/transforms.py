"""数据增强与预处理。训练用 RandAugment + 随机擦除；验证/测试用确定性变换。"""
from __future__ import annotations

from torchvision import transforms
from torchvision.transforms import InterpolationMode

_NORM_MEAN = [0.485, 0.456, 0.406]
_NORM_STD = [0.229, 0.224, 0.225]


def build_transforms(
    image_size: int = 384,
    *,
    train: bool = True,
    aug: str = "randaug",
    erase: float = 0.0,
    randaug_n: int = 2,
    randaug_m: int = 9,
    use_bbox: bool = False,
) -> transforms.Compose:
    """构建预处理/增强流水线。

    - 验证/测试：Resize(BICUBIC) -> CenterCrop，保持与线上推理一致。
    - 训练：RandomResizedCrop + 随机水平翻转 + [RandAugment] + ToTensor + Normalize + [RandomErasing]。
      当已做 bbox 裁剪时，作物已聚焦目标，crop scale 收紧到 (0.85, 1.0) 避免过度放大背景抖动。
    """
    if not train:
        return transforms.Compose(
            [
                transforms.Resize(image_size, interpolation=InterpolationMode.BICUBIC),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                transforms.Normalize(_NORM_MEAN, _NORM_STD),
            ]
        )

    scale = (0.85, 1.0) if use_bbox else (0.6, 1.0)
    ops: list = [
        transforms.RandomResizedCrop(
            image_size, scale=scale, interpolation=InterpolationMode.BICUBIC
        ),
        transforms.RandomHorizontalFlip(0.5),
    ]
    if aug == "randaug":
        try:
            ops.append(
                transforms.RandAugment(num_ops=randaug_n, magnitude=randaug_m)
            )
        except Exception:
            pass
    ops += [
        transforms.ToTensor(),
        transforms.Normalize(_NORM_MEAN, _NORM_STD),
    ]
    if erase and erase > 0:
        ops.append(transforms.RandomErasing(p=erase, value="random"))
    return transforms.Compose(ops)
