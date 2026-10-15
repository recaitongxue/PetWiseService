"""采样器：类平衡采样 + 分布式（DDP）类平衡采样。

类平衡采样按类频的 -alpha 次幂加权，缓解 THU-Dogs / 猫数据集的长尾问题。
分布式版本在每轮重建权重序列，并按 rank 跨步切片，保证各卡都拿到类平衡且不重叠的子集。
"""
from __future__ import annotations

from collections import Counter

import torch
from torch.utils.data import Sampler, WeightedRandomSampler


def make_balanced_sampler(
    targets: list[int],
    *,
    alpha: float = 0.5,
    num_samples: int | None = None,
    generator: torch.Generator | None = None,
) -> WeightedRandomSampler:
    counts = Counter(targets)
    weights = [1.0 / (counts[t] ** alpha) for t in targets]
    return WeightedRandomSampler(
        weights,
        num_samples=num_samples if num_samples is not None else len(weights),
        replacement=True,
        generator=generator,
    )


class DistributedBalancedSampler(Sampler):
    """DDP 下的类平衡采样器：每轮重建加权序列，按 rank 跨步切片分发到各卡。"""

    def __init__(
        self,
        targets: list[int],
        *,
        num_replicas: int = 1,
        rank: int = 0,
        alpha: float = 0.5,
        num_samples: int | None = None,
        seed: int = 42,
        shuffle: bool = True,
    ):
        self.targets = targets
        self.num_replicas = num_replicas
        self.rank = rank
        self.alpha = alpha
        self.num_samples_total = num_samples if num_samples is not None else len(targets)
        self.seed = seed
        self.shuffle = shuffle
        self.epoch = 0
        self.indices: list[int] = []
        self._build()

    def _weights(self) -> list[float]:
        counts = Counter(self.targets)
        return [1.0 / (counts[t] ** self.alpha) for t in self.targets]

    def _build(self) -> None:
        g = torch.Generator()
        g.manual_seed(self.seed + self.epoch * 100000 + self.rank)
        w = torch.tensor(self._weights(), dtype=torch.double)
        # 按权重有放回抽取 num_samples_total 个全局索引
        full = torch.multinomial(
            w, self.num_samples_total, replacement=True, generator=g
        ).tolist()
        # 各 rank 取跨步切片，保证不重叠且整体覆盖完整一轮
        self.indices = full[self.rank :: self.num_replicas]

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch
        self._build()

    def __iter__(self):
        if self.shuffle:
            # 仅打乱本 rank 片段顺序
            g = torch.Generator()
            g.manual_seed(self.seed + self.epoch * 7 + self.rank * 13)
            order = torch.randperm(len(self.indices), generator=g).tolist()
            return (self.indices[i] for i in order)
        return iter(self.indices)

    def __len__(self) -> int:
        return len(self.indices)
