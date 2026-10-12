"""模型组装工厂。

把"选骨干 + 换分类头"这件事收口在一处，
训练、评测、导出三方共用同一份定义，避免导出的图和训练的模型不一致。
"""

from __future__ import annotations

from typing import Any

SUPPORTED_BACKBONES = [
    "resnet50",
    "efficientnet_b0",
    "efficientnet_b3",
    "efficientnet_b4",
    "convnext_tiny",
    "swin_t",
    "mobilenet_v3_large",
]


def build_model(num_classes: int, *, backbone: str = "resnet50", pretrained: bool = True) -> Any:
    """构造分类模型。

    torch 在导出与训练的容器里都存在，这里不做降级：
    离线工程本就该假定训练依赖齐备。
    """
    import torch
    from torchvision import models

    if backbone not in SUPPORTED_BACKBONES:
        raise ValueError(f"不支持的骨干网络: {backbone}，可选 {SUPPORTED_BACKBONES}")

    weights = "DEFAULT" if pretrained else None
    if backbone == "resnet50":
        model = models.resnet50(weights=weights)
        model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    elif backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=weights)
        model.classifier[1] = torch.nn.Linear(
            model.classifier[1].in_features, num_classes
        )
    elif backbone == "convnext_tiny":
        model = models.convnext_tiny(weights=weights)
        model.classifier[2] = torch.nn.Linear(
            model.classifier[2].in_features, num_classes
        )
    elif backbone == "efficientnet_b3":
        model = models.efficientnet_b3(weights=weights)
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
    elif backbone == "efficientnet_b4":
        model = models.efficientnet_b4(weights=weights)
        model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
    elif backbone == "swin_t":
        model = models.swin_t(weights=weights)
        model.head = torch.nn.Linear(model.head.in_features, num_classes)
    else:
        model = models.mobilenet_v3_large(weights=weights)
        model.classifier[-1] = torch.nn.Linear(
            model.classifier[-1].in_features, num_classes
        )

    return model
