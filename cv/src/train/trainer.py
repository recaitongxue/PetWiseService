"""训练循环。

只保留必要的骨架：AMP 混合精度、余弦退火、按验证集 top-1 保存最优、早停、
断点续训。刻意不引入 Trainer 框架——毕设规模下，看得见的循环更好调、更好讲。
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader


@dataclass
class TrainConfig:
    epochs: int = 30
    lr: float = 3e-4
    weight_decay: float = 1e-4
    patience: int = 6              # 早停轮数
    amp: bool = True               # 混合精度
    num_classes: int = 10
    backbone: str = "resnet50"
    label_smoothing: float = 0.05
    mixup: float = 0.0              # >0 开启 Mixup（长尾数据增强，推荐 0.2）
    cutmix: float = 0.0             # >0 开启 CutMix（空间增强，优先于 mixup）
    output_dir: Path = Path("artifacts")
    csv_name: str = "train-history.csv"

    history: list[dict] = field(default_factory=list)


class Trainer:
    def __init__(self, model: nn.Module, cfg: TrainConfig, resume_from: Path | None = None) -> None:
        self.model = model
        self.cfg = cfg
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # mixup/cutmix 自带软标签，与 label smoothing 叠加会过度平滑，故自动关闭
        self.smoothing = 0.0 if (cfg.mixup > 0 or cfg.cutmix > 0) else cfg.label_smoothing
        if (cfg.mixup > 0 or cfg.cutmix > 0) and self.smoothing != cfg.label_smoothing:
            print(f"[train] 启用 mixup/cutmix，label smoothing {cfg.label_smoothing} -> 0")
        self.criterion = nn.CrossEntropyLoss(label_smoothing=self.smoothing)
        self.optimizer = torch.optim.AdamW(
            model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
        )
        amp_dev = self.device.type  # cuda / cpu；CPU 上 enabled=False，无副作用
        self.amp_dev = amp_dev
        self.scaler = torch.amp.GradScaler(amp_dev, enabled=cfg.amp and self.device.type == "cuda")

        self.start_epoch = 1
        if resume_from is not None and resume_from.is_file():
            state = torch.load(resume_from, map_location="cpu")
            model.load_state_dict(state.get("state_dict", state))
            self.start_epoch = state.get("epoch", 0) + 1
            print(f"[resume] 从第 {self.start_epoch} 轮继续训练")

    def _use_amp(self) -> bool:
        return self.cfg.amp and self.device.type == "cuda"

    # ── 数据增强（长尾样本少，mixup/cutmix 提升泛化）─────────
    def _mixup(self, images: torch.Tensor, targets: torch.Tensor):
        lam = float(np.random.beta(self.cfg.mixup, self.cfg.mixup))
        perm = torch.randperm(images.size(0), device=images.device)
        mixed = lam * images + (1 - lam) * images[perm]
        return mixed, targets, targets[perm], lam

    def _cutmix(self, images: torch.Tensor, targets: torch.Tensor):
        lam = float(np.random.beta(self.cfg.cutmix, self.cfg.cutmix))
        perm = torch.randperm(images.size(0), device=images.device)
        bbx1, bby1, bbx2, bby2 = self._rand_bbox(images.size(2), images.size(3), lam)
        mixed = images.clone()
        mixed[:, :, bbx1:bbx2, bby1:bby2] = images[perm, :, bbx1:bbx2, bby1:bby2]
        # 用实际裁剪面积修正 lambda，使两个目标的损失权重更准确
        lam = 1 - ((bbx2 - bbx1) * (bby2 - bby1) / (images.size(2) * images.size(3)))
        return mixed, targets, targets[perm], lam

    @staticmethod
    def _rand_bbox(w: int, h: int, lam: float) -> tuple[int, int, int, int]:
        cut_ratio = (1 - lam) ** 0.5
        cut_w, cut_h = int(w * cut_ratio), int(h * cut_ratio)
        cx, cy = np.random.randint(w), np.random.randint(h)
        bbx1 = max(cx - cut_w // 2, 0)
        bby1 = max(cy - cut_h // 2, 0)
        bbx2 = min(cx + cut_w // 2, w)
        bby2 = min(cy + cut_h // 2, h)
        return bbx1, bby1, bbx2, bby2

    # ── 单轮 ─────────────────────────────────────────────────
    def train_epoch(self, loader: DataLoader, scheduler: CosineAnnealingLR) -> float:
        self.model.train()
        total, correct, samples = 0.0, 0, 0

        for images, targets in loader:
            images, targets = images.to(self.device), targets.to(self.device)
            self.optimizer.zero_grad()

            use_mix = False
            if self.cfg.cutmix > 0:
                images, targets_a, targets_b, lam = self._cutmix(images, targets)
                use_mix = True
            elif self.cfg.mixup > 0:
                images, targets_a, targets_b, lam = self._mixup(images, targets)
                use_mix = True

            with torch.amp.autocast(self.amp_dev, enabled=self._use_amp()):
                outputs = self.model(images)
                if use_mix:
                    loss = lam * self.criterion(outputs, targets_a) + (1 - lam) * self.criterion(
                        outputs, targets_b
                    )
                else:
                    loss = self.criterion(outputs, targets)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()

            total += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == targets).sum().item()
            samples += images.size(0)

        scheduler.step()
        return correct / max(1, samples)

    @torch.no_grad()
    def validate(self, loader: DataLoader) -> tuple[float, float, float]:
        self.model.eval()
        correct, top5_correct, samples, total = 0, 0, 0, 0.0

        for images, targets in loader:
            images, targets = images.to(self.device), targets.to(self.device)
            outputs = self.model(images)
            loss = self.criterion(outputs, targets)

            top5_correct += outputs.topk(5, dim=1)[1].eq(targets.view(-1, 1)).sum().item()
            correct += (outputs.argmax(1) == targets).sum().item()
            total += loss.item() * images.size(0)
            samples += images.size(0)

        return correct / max(1, samples), top5_correct / max(1, samples), total / max(1, samples)

    # ── 全量 ─────────────────────────────────────────────────
    def fit(self, train_loader: DataLoader, val_loader: DataLoader) -> dict:
        scheduler = CosineAnnealingLR(self.optimizer, T_max=max(1, self.cfg.epochs - self.start_epoch + 1))
        best_top1, no_improve, started = 0.0, 0, time.time()

        csv_path = self.cfg.output_dir / self.cfg.csv_name
        self.cfg.output_dir.mkdir(parents=True, exist_ok=True)
        write_header = not csv_path.exists()
        csv_file = csv_path.open("a", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        if write_header:
            writer.writerow(["epoch", "trainAcc", "valAcc", "valTop5", "valLoss"])

        for epoch in range(self.start_epoch, self.cfg.epochs + 1):
            train_acc = self.train_epoch(train_loader, scheduler)
            val_acc, val_top5, val_loss = self.validate(val_loader)

            improved = val_acc > best_top1
            if improved:
                best_top1 = val_acc
                no_improve = 0
                self._save_checkpoint(epoch)
            else:
                no_improve += 1

            self.cfg.history.append(
                {
                    "epoch": epoch,
                    "trainAcc": round(train_acc, 4),
                    "valAcc": round(val_acc, 4),
                    "valTop5": round(val_top5, 4),
                    "valLoss": round(val_loss, 4),
                }
            )
            writer.writerow([epoch, round(train_acc, 4), round(val_acc, 4), round(val_top5, 4), round(val_loss, 4)])
            csv_file.flush()

            print(
                f"epoch {epoch:>3} train={train_acc:.4f} val={val_acc:.4f} "
                f"top5={val_top5:.4f} best={best_top1:.4f} {'*' if improved else ''}"
            )

            if no_improve >= self.cfg.patience:
                print(f"[early stop] {self.cfg.patience} 轮未提升，停止训练")
                break

        csv_file.close()
        report = {
            "bestTop1": round(best_top1, 4),
            "epochs": len(self.cfg.history),
            "elapsedSec": round(time.time() - started, 1),
            "history": self.cfg.history,
        }
        (self.cfg.output_dir / "train-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return report

    def _save_checkpoint(self, epoch: int) -> None:
        self.cfg.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.cfg.output_dir / "best.pt"
        torch.save(
            {
                "epoch": epoch,
                "state_dict": self.model.state_dict(),
                "backbone": self.cfg.backbone,
                "num_classes": self.cfg.num_classes,
            },
            path,
        )
