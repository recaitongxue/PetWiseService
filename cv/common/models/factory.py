"""骨干网络工厂。

支持论文级强骨干（ImageNet 预训练权重）：ConvNeXt-L/B、Swin-B、EfficientNet-V2-L、
ViT-B/16、MaxViT-T、ResNet-50。统一替换分类头为 num_classes 维，便于细粒度多分类。

选型参考（ImageNet top-1，仅作选型依据，非本项目实测）：
  resnet50           80.9   基线对照，轻量
  convnext_base      83.8   现代 CNN，显存友好
  convnext_large     84.3   本项目狗模型默认骨干（本机 64GB 显存可上 384px）
  swin_b             83.5   Transformer，长尾/细粒度常有优势
  efficientnet_v2_l  84.9   本项目猫模型默认骨干（参数少、精度高）
  vit_b_16           84.5   纯 Transformer，需较强增强与长训练
  maxvit_t           83.1   混合卷积-注意力，轻量
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torchvision.models as models

# 骨干 -> (构造器, 权重枚举)
_BUILDERS = {
    "resnet50": (models.resnet50, models.ResNet50_Weights.DEFAULT),
    "convnext_base": (models.convnext_base, models.ConvNeXt_Base_Weights.DEFAULT),
    "convnext_large": (models.convnext_large, models.ConvNeXt_Large_Weights.DEFAULT),
    "swin_b": (models.swin_b, models.Swin_B_Weights.DEFAULT),
    "efficientnet_v2_l": (models.efficientnet_v2_l, models.EfficientNet_V2_L_Weights.DEFAULT),
    "vit_b_16": (models.vit_b_16, models.ViT_B_16_Weights.DEFAULT),
    "maxvit_t": (models.maxvit_t, models.MaxVit_T_Weights.DEFAULT),
}

SUPPORTED_BACKBONES = list(_BUILDERS.keys())


def _set_last_linear(obj, attr: str, num_classes: int) -> None:
    """将 obj.<attr>（Linear 或 末层为 Linear 的 Sequential）替换为 num_classes 维线性层。"""
    mod = getattr(obj, attr)
    if isinstance(mod, nn.Sequential):
        last = mod[-1]
        in_f = last.in_features
        mod[-1] = nn.Linear(in_f, num_classes)
    elif isinstance(mod, nn.Linear):
        in_f = mod.in_features
        setattr(obj, attr, nn.Linear(in_f, num_classes))
    else:
        raise ValueError(f"无法识别的分类头类型: {type(mod)}")


def _replace_head(model: nn.Module, backbone: str, num_classes: int) -> nn.Module:
    bn = backbone.lower()
    if bn.startswith("resnet"):
        _set_last_linear(model, "fc", num_classes)
    elif bn.startswith("convnext") or bn.startswith("efficientnet") or bn.startswith("maxvit"):
        _set_last_linear(model, "classifier", num_classes)
    elif bn.startswith("swin"):
        _set_last_linear(model, "head", num_classes)
    elif bn.startswith("vit"):
        _set_last_linear(model, "heads", num_classes)
    else:
        raise ValueError(f"无法替换分类头：未知骨干 {backbone}")
    return model


def build_model(
    backbone: str,
    num_classes: int,
    *,
    pretrained: bool = True,
) -> nn.Module:
    if backbone not in _BUILDERS:
        raise ValueError(
            f"不支持的骨干 {backbone}，可选：{SUPPORTED_BACKBONES}"
        )
    builder, weights = _BUILDERS[backbone]
    model = builder(weights=weights if pretrained else None)
    model = _replace_head(model, backbone, num_classes)
    return model


def get_backbone_info(backbone: str) -> dict:
    return {
        "name": backbone,
        "imagenet_top1": {
            "resnet50": 80.9,
            "convnext_base": 83.8,
            "convnext_large": 84.3,
            "swin_b": 83.5,
            "efficientnet_v2_l": 84.9,
            "vit_b_16": 84.5,
            "maxvit_t": 83.1,
        }.get(backbone, None),
    }
