"""自研损失函数：类别均衡 Focal 损失（论文创新点）。

组合两篇经典工作：
  - Focal Loss (Lin et al., ICCV 2017)：以 (1 - p_t)^gamma 降低易分样本权重，聚焦难例。
  - Class-Balanced Loss (Cui et al., CVPR 2019)：以"有效样本数" (1-beta^n)/(1-beta)
    对少数类加权，缓解长尾。

最终逐样本权重 = 类别均衡权重 × Focal 调制因子，可与 label smoothing 兼容。
零额外参数、不增加推理成本，仅作用于训练阶段。
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    def __init__(self, gamma: float = 2.0, label_smoothing: float = 0.0, reduction: str = "mean"):
        super().__init__()
        self.gamma = gamma
        self.label_smoothing = label_smoothing
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_probs = F.log_softmax(logits, dim=1)
        nll = -log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)  # -log p_t
        if self.label_smoothing > 0:
            smooth = (1 - self.label_smoothing) * nll + self.label_smoothing * (
                -log_probs.mean(dim=1)
            )
        else:
            smooth = nll
        p_t = torch.exp(-nll)
        focal = (1.0 - p_t) ** self.gamma
        loss = focal * smooth
        return loss.mean() if self.reduction == "mean" else loss.sum()


class ClassBalancedFocalLoss(nn.Module):
    """类别均衡 Focal 损失（Cui 2019 + Lin 2017）。

    class_counts: 每个类别的训练样本数（用于计算有效样本数权重）。
    beta: 有效样本数系数，越接近 1 越偏向少数类（常用 0.9999）。
    gamma: Focal 聚焦参数。
    """

    def __init__(
        self,
        num_classes: int,
        class_counts: list[int] | None = None,
        beta: float = 0.9999,
        gamma: float = 2.0,
        label_smoothing: float = 0.0,
        reduction: str = "mean",
    ):
        super().__init__()
        self.num_classes = num_classes
        self.beta = beta
        self.gamma = gamma
        self.label_smoothing = label_smoothing
        self.reduction = reduction
        self.register_buffer("cb_weight", self._compute_cb_weight(class_counts))

    @staticmethod
    def _compute_cb_weight(class_counts: list[int] | None) -> torch.Tensor:
        if not class_counts:
            return torch.ones(1)  # 退化为无加权
        counts = torch.tensor(class_counts, dtype=torch.float)
        beta = 0.9999
        effective_num = 1.0 - torch.pow(beta, counts)
        weights = (1.0 - beta) / (effective_num + 1e-8)
        weights = weights / weights.sum() * len(class_counts)  # 归一化到均值 1
        return weights

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_probs = F.log_softmax(logits, dim=1)
        nll = -log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
        if self.label_smoothing > 0:
            smooth = (1 - self.label_smoothing) * nll + self.label_smoothing * (
                -log_probs.mean(dim=1)
            )
        else:
            smooth = nll
        p_t = torch.exp(-nll)
        focal = (1.0 - p_t) ** self.gamma
        if self.cb_weight.numel() == 1:
            weight = 1.0
        else:
            weight = self.cb_weight.to(logits.device)[targets]
        loss = weight * focal * smooth
        return loss.mean() if self.reduction == "mean" else loss.sum()


def build_criterion(
    name: str,
    num_classes: int,
    class_counts: list[int] | None = None,
    label_smoothing: float = 0.0,
    focal_gamma: float = 2.0,
    cb_beta: float = 0.9999,
):
    if name == "ce":
        return nn.CrossEntropyLoss(label_smoothing=label_smoothing)
    if name == "focal":
        return FocalLoss(gamma=focal_gamma, label_smoothing=label_smoothing)
    if name == "cb_focal":
        return ClassBalancedFocalLoss(
            num_classes=num_classes,
            class_counts=class_counts,
            beta=cb_beta,
            gamma=focal_gamma,
            label_smoothing=label_smoothing,
        )
    raise ValueError(f"未知损失 {name}，可选 ce|focal|cb_focal")
