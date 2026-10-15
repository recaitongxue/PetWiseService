"""训练引擎：支持 DDP、EMA、梯度累积、AMP 混合精度、cosine+warmup 调度、早停。

设计要点：
- 主进程（rank0）负责写文件、打日志、保存最优权重；其余进程静默。
- 验证与保存均使用 EMA 权重（保证 early stopping 选中的即最终上线权重）。
- 梯度累积让双 5090 上也能用较大有效 batch（batch×world×accum）。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ..eval import evaluate as evaluate_mod


class _EMA:
    """指数移动平均，仅维护可训练参数。"""

    def __init__(self, model: nn.Module, decay: float = 0.999):
        self.decay = decay
        self.shadow = {k: v.detach().clone() for k, v in model.state_dict().items()}
        self._backup: dict | None = None

    @torch.no_grad()
    def update(self, model: nn.Module):
        sd = model.state_dict()
        for k in self.shadow:
            if k in sd:
                self.shadow[k] = self.decay * self.shadow[k] + (1 - self.decay) * sd[k].detach()

    @torch.no_grad()
    def apply_and_backup(self, model: nn.Module):
        """把 EMA 权重写入模型，并备份当前（训练）权重以便恢复。"""
        self._backup = {k: v.detach().clone() for k, v in model.state_dict().items()}
        sd = model.state_dict()
        for k in self.shadow:
            if k in sd:
                sd[k].copy_(self.shadow[k])

    @torch.no_grad()
    def restore(self, model: nn.Module):
        if self._backup is None:
            return
        sd = model.state_dict()
        for k, v in self._backup.items():
            if k in sd:
                sd[k].copy_(v)
        self._backup = None

    def state_dict(self):
        return self.shadow


class Trainer:
    def __init__(
        self,
        *,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler,
        cfg: dict,
        device: torch.device,
        rank: int = 0,
        world_size: int = 1,
        is_main: bool = True,
        output_dir: Path,
        class_counts: list[int] | None = None,
        kind: str = "dog",
    ):
        self.model = model
        self.kind = kind
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.cfg = cfg
        self.device = device
        self.rank = rank
        self.world_size = world_size
        self.is_main = is_main
        self.output_dir = Path(output_dir)
        self.class_counts = class_counts
        self.use_amp = bool(cfg.get("amp", True)) and device.type == "cuda"
        self.scaler = torch.amp.GradScaler("cuda") if self.use_amp else None
        self.grad_accum = max(1, int(cfg.get("grad_accum", 1)))
        self.start_epoch = 1
        self.best_top1 = 0.0
        self.ema = _EMA(model, cfg.get("ema", 0.0)) if cfg.get("ema", 0.0) > 0 else None

    def _head_param_names(self):
        return {n for n, _ in self.model.named_parameters()
                if any(k in n.lower() for k in ("classifier", "fc", "head"))}

    @torch.no_grad()
    def _set_frozen(self, frozen: bool):
        head_names = self._head_param_names()
        for n, p in self.model.named_parameters():
            p.requires_grad = (not frozen) or (n in head_names)

    def _save_checkpoint(self, epoch: int, state_dict: dict):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ckpt = {
            "epoch": epoch,
            "state_dict": state_dict,
            "optimizer": self.optimizer.state_dict(),
            "best_top1": self.best_top1,
        }
        torch.save(ckpt, self.output_dir / "best-checkpoint.pt")

    def resume(self, path: str | Path):
        ckpt = torch.load(path, map_location=self.device)
        self.model.load_state_dict(ckpt["state_dict"])
        self.optimizer.load_state_dict(ckpt["optimizer"])
        self.start_epoch = ckpt.get("epoch", 0) + 1
        self.best_top1 = ckpt.get("best_top1", 0.0)
        if self.is_main:
            print(f"[resume] 从第 {self.start_epoch} 轮继续训练")

    def train_epoch(self) -> float:
        self.model.train()
        correct, total, running = 0, 0, 0.0
        optimizer = self.optimizer
        accum = self.grad_accum
        optimizer.zero_grad(set_to_none=True)
        loader = self.train_loader
        if self.is_main:
            loader = _tqdm_like(loader, desc=f"epoch {self.cur_epoch}")

        for step, (imgs, targets) in enumerate(loader):
            imgs = imgs.to(self.device, non_blocking=True)
            targets = targets.to(self.device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=self.use_amp):
                logits = self.model(imgs)
                loss = self.criterion(logits, targets) / accum
            if self.scaler is not None:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
            running += float(loss) * accum
            total += targets.size(0)
            correct += int(logits.argmax(1).eq(targets).sum())

            if (step + 1) % accum == 0 or (step + 1) == len(self.train_loader):
                if self.scaler is not None:
                    self.scaler.step(optimizer)
                    self.scaler.update()
                else:
                    optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        return correct / max(1, total)

    @torch.no_grad()
    def validate(self, loader: DataLoader):
        self.model.eval()
        correct1 = correct5 = total = 0
        running = 0.0
        for imgs, targets in loader:
            imgs = imgs.to(self.device, non_blocking=True)
            targets = targets.to(self.device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=self.use_amp):
                logits = self.model(imgs)
                loss = self.criterion(logits, targets)
            running += float(loss) * imgs.size(0)
            total += targets.size(0)
            topk = logits.topk(5, dim=1).indices
            correct1 += int(topk[:, 0].eq(targets).sum())
            correct5 += int(topk.eq(targets.unsqueeze(1)).any(dim=1).sum())
        return correct1 / max(1, total), correct5 / max(1, total), running / max(1, total)

    def fit(self, test_loader=None, class_names=None):
        history = []
        no_improve = 0
        patience = int(self.cfg.get("patience", 15))
        started = time.time()
        if self.is_main:
            print(f"[train] 开始训练  world_size={self.world_size}  amp={self.use_amp}  "
                  f"ema={self.cfg.get('ema', 0.0)}  grad_accum={self.grad_accum}")

        for epoch in range(self.start_epoch, int(self.cfg.get("epochs", 100)) + 1):
            self.cur_epoch = epoch
            if self.cfg.get("freeze_epochs") and epoch <= self.cfg.get("freeze_epochs", 0):
                self._set_frozen(True)
            else:
                self._set_frozen(False)
            if hasattr(self.train_loader, "sampler") and hasattr(self.train_loader.sampler, "set_epoch"):
                self.train_loader.sampler.set_epoch(epoch)

            train_acc = self.train_epoch()
            self.scheduler.step()

            # 验证与保存均使用 EMA 权重
            if self.ema is not None:
                self.ema.update(self.model)
                self.ema.apply_and_backup(self.model)
                val_acc, val_top5, val_loss = self.validate(self.val_loader)
                save_state = self.ema.state_dict()
                self.ema.restore(self.model)
            else:
                val_acc, val_top5, val_loss = self.validate(self.val_loader)
                save_state = self.model.state_dict()

            improved = val_acc > self.best_top1
            if improved:
                self.best_top1 = val_acc
                no_improve = 0
                if self.is_main:
                    self._save_checkpoint(epoch, save_state)
            else:
                no_improve += 1

            lr = self.optimizer.param_groups[0]["lr"]
            if self.is_main:
                print(f"epoch {epoch:>3} lr={lr:.2e} train={train_acc:.4f} "
                      f"val={val_acc:.4f} top5={val_top5:.4f} best={self.best_top1:.4f}"
                      f"{'*' if improved else ''}")
            history.append({
                "epoch": epoch, "lr": round(lr, 8), "trainAcc": round(train_acc, 4),
                "valAcc": round(val_acc, 4), "valTop5": round(val_top5, 4),
                "valLoss": round(val_loss, 4),
            })
            if no_improve >= patience:
                if self.is_main:
                    print(f"[early stop] {patience} 轮未提升，停止")
                break

        if self.is_main:
            report = {
                "bestValTop1": round(self.best_top1, 4),
                "epochs": len(history),
                "elapsedSec": round(time.time() - started, 1),
                "history": history,
            }
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "train-report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if test_loader is not None and class_names is not None:
                self._final_eval(test_loader, class_names)

    def _final_eval(self, test_loader, class_names):
        tta = bool(self.cfg.get("tta", True))
        if self.ema is not None:
            self.ema.apply_and_backup(self.model)
            evaluate_mod.evaluate_full(
                self.model, test_loader, tta=tta,
                class_names=class_names, train_counts=self.class_counts,
                output_dir=self.output_dir, split="test", kind=self.kind,
            )
            self.ema.restore(self.model)
        else:
            evaluate_mod.evaluate_full(
                self.model, test_loader, tta=tta,
                class_names=class_names, train_counts=self.class_counts,
                output_dir=self.output_dir, split="test", kind=self.kind,
            )


def _tqdm_like(loader, desc: str):
    try:
        from tqdm import tqdm
        return tqdm(loader, desc=desc)
    except Exception:
        return loader
