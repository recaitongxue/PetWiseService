"""训练 / 评测入口。

用法（由 scripts/train.sh 调用，自动处理 DDP）：
  python -m common.train.cli --kind dog --config dog/configs/train.yaml
  torchrun --nproc_per_node=2 -m common.train.cli --kind dog --config dog/configs/train.yaml
  python -m common.train.cli --kind dog --config dog/configs/train.yaml --only-eval \
         --weights artifacts/artifacts/best-dog.pt

DDP 通过环境变量（WORLD_SIZE/LOCAL_RANK/RANK）由 torchrun 注入，自动识别。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.distributed as dist
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from common.data import labels as labels_mod  # noqa: E402
from common.data import transforms as T  # noqa: E402
from common.data.dataset import build_dataset  # noqa: E402
from common.data.sampler import DistributedBalancedSampler, make_balanced_sampler  # noqa: E402
from common.models import factory as model_factory  # noqa: E402
from common.models.loss import build_criterion  # noqa: E402
from common.train.engine import Trainer  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=["dog", "cat"])
    p.add_argument("--config", type=Path, default=None, help="训练配置 yaml")
    p.add_argument("--dataset-config", type=Path, default=None, help="数据配置 yaml（默认 <kind>/configs/dataset.yaml）")
    p.add_argument("--root", type=Path, default=None, help="数据根目录覆盖（如 /data/<kind>）")
    p.add_argument("--artifacts", type=Path, default=ROOT / "artifacts" / "artifacts")
    p.add_argument("--only-eval", action="store_true")
    p.add_argument("--weights", type=Path, default=None)
    p.add_argument("--resume", type=Path, default=None)
    p.add_argument("--batch-size", type=int, default=None)
    p.add_argument("--image-size", type=int, default=None)
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--loss", type=str, default=None, choices=["ce", "focal", "cb_focal"])
    p.add_argument("--backbone", type=str, default=None)
    return p.parse_args()


def setup_dist():
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    rank = int(os.environ.get("RANK", "0"))
    if world_size > 1:
        dist.init_process_group(backend="nccl")
        torch.cuda.set_device(local_rank)
    return world_size, local_rank, rank


def build_optimizer(model, cfg):
    head_names = {n for n, _ in model.named_parameters() if any(k in n.lower() for k in ("classifier", "fc", "head"))}
    base_lr = float(cfg.get("lr", 1e-4))
    head_mult = float(cfg.get("lr_head_multiplier", 10.0))
    groups = [
        {"params": [p for n, p in model.named_parameters() if n in head_names], "lr": base_lr * head_mult},
        {"params": [p for n, p in model.named_parameters() if n not in head_names], "lr": base_lr},
    ]
    return torch.optim.AdamW(groups, weight_decay=float(cfg.get("weight_decay", 0.05)))


def build_scheduler(optimizer, cfg, epochs):
    warmup = int(cfg.get("warmup_epochs", 5))
    lr0 = optimizer.param_groups[0]["lr"]
    lr_min = lr0 * 1e-3

    def lr_lambda(epoch):
        if epoch < warmup:
            return (epoch + 1) / max(1, warmup)
        progress = (epoch - warmup) / max(1, epochs - warmup)
        return lr_min / lr0 + (1 - lr_min / lr0) * 0.5 * (1 + math.cos(math.pi * progress))

    return LambdaLR(optimizer, lr_lambda)


def main():
    args = parse_args()
    world_size, local_rank, rank = setup_dist()
    is_main = rank == 0
    device = torch.device("cuda", local_rank) if (torch.cuda.is_available() and world_size > 0) else torch.device("cpu")

    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # 配置
    config_path = args.config or (ROOT / args.kind / "configs" / "train.yaml")
    ds_config_path = args.dataset_config or (ROOT / args.kind / "configs" / "dataset.yaml")
    cfg = labels_mod.load_dataset_yaml(config_path)
    ds = labels_mod.load_dataset_yaml(ds_config_path)
    cfg["dataset"] = ds

    # 命令行覆盖
    if args.backbone: cfg["backbone"] = args.backbone
    if args.loss: cfg["loss_name"] = args.loss
    if args.batch_size: cfg["batch_size"] = args.batch_size
    if args.image_size: cfg["dataset"]["image_size"] = args.image_size
    if args.epochs: cfg["epochs"] = args.epochs

    image_size = int(cfg["dataset"]["image_size"])
    num_classes = int(cfg["dataset"].get("num_classes", 0)) or int(
        labels_mod.load_labels(args.kind, args.artifacts)["num_classes"]
    )

    # 标签（缺失则自动构建）
    try:
        labels = labels_mod.load_labels(args.kind, args.artifacts)
    except FileNotFoundError:
        labels = labels_mod.build_labels(
            args.kind, cfg["dataset"].get("root", ROOT / "datasets" / args.kind), args.artifacts
        )
    num_classes = len(labels["names"])
    class_names = labels["names"]

    if is_main:
        print(f"[init] kind={args.kind}  backbone={cfg['backbone']}  "
              f"image_size={image_size}  num_classes={num_classes}  "
              f"DDP={'开' if world_size>1 else '关'}(world={world_size})  device={device}")

    # 数据集
    use_bbox = bool(cfg["dataset"].get("use_bbox", False))
    train_tf = T.build_transforms(image_size, train=True, aug=cfg.get("aug", "randaug"),
                                  erase=float(cfg.get("erase", 0.0)),
                                  randaug_n=int(cfg.get("randaug_n", 2)),
                                  randaug_m=int(cfg.get("randaug_m", 9)),
                                  use_bbox=use_bbox)
    eval_tf = T.build_transforms(image_size, train=False)

    train_ds = build_dataset(args.kind, "train", cfg, args.artifacts, train_tf)
    val_ds = build_dataset(args.kind, "val", cfg, args.artifacts, eval_tf)
    test_ds = build_dataset(args.kind, "test", cfg, args.artifacts, eval_tf)

    # 类别计数（用于类别均衡损失 / 长尾分段）
    train_targets = [s[1] for s in getattr(train_ds, "samples", [])]
    if not train_targets:
        train_targets = [0] * len(train_ds)
    class_counts = [0] * num_classes
    for t in train_targets:
        class_counts[t] += 1

    # 采样器（训练）
    batch_size = int(cfg.get("batch_size", 32))
    num_workers = int(ds.get("dataloader", {}).get("num_workers", 8))
    if world_size > 1:
        train_sampler = DistributedBalancedSampler(
            train_targets, num_replicas=world_size, rank=rank,
            alpha=float(cfg.get("balance_alpha", 0.5)),
            seed=seed,
        )
    elif cfg.get("balance", True):
        train_sampler = make_balanced_sampler(train_targets, alpha=float(cfg.get("balance_alpha", 0.5)))
    else:
        train_sampler = None

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=(train_sampler is None),
        sampler=train_sampler, num_workers=num_workers, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(val_ds, batch_size=batch_size * 2, shuffle=False,
                            num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_ds, batch_size=batch_size * 2, shuffle=False,
                             num_workers=num_workers, pin_memory=True)

    # 模型
    model = model_factory.build_model(cfg["backbone"], num_classes, pretrained=True)
    model.to(device)
    if world_size > 1:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank])

    criterion = build_criterion(
        cfg.get("loss_name", "cb_focal"), num_classes=num_classes,
        class_counts=class_counts,
        label_smoothing=float(cfg.get("label_smoothing", 0.1)),
        focal_gamma=float(cfg.get("focal_gamma", 2.0)),
        cb_beta=float(cfg.get("cb_beta", 0.9999)),
    )

    optimizer = build_optimizer(model, cfg)
    scheduler = build_scheduler(optimizer, cfg, int(cfg.get("epochs", 100)))
    output_dir = args.artifacts

    if args.only_eval:
        weights = args.weights or (output_dir / f"best-{args.kind}.pt")
        sd = torch.load(weights, map_location=device)
        state = sd.get("state_dict", sd)
        model.load_state_dict(state, strict=False)
        if is_main:
            print(f"[eval] 加载权重 {weights}")
        from common.eval import evaluate as evaluate_mod
        evaluate_mod.evaluate_full(
            model, test_loader, tta=bool(cfg.get("tta", True)),
            class_names=class_names, train_counts=class_counts,
            output_dir=output_dir, split="test", kind=args.kind,
        )
        if world_size > 1:
            dist.destroy_process_group()
        return

    trainer = Trainer(
        model=model, train_loader=train_loader, val_loader=val_loader,
        criterion=criterion, optimizer=optimizer, scheduler=scheduler, cfg=cfg,
        device=device, rank=rank, world_size=world_size, is_main=is_main,
        output_dir=output_dir, class_counts=class_counts, kind=args.kind,
    )
    if args.resume:
        trainer.resume(args.resume)
    trainer.fit(test_loader=test_loader, class_names=class_names)

    if is_main:
        # 同时导出最终权重到约定的 best-<kind>.pt
        best_ckpt = output_dir / "best-checkpoint.pt"
        if best_ckpt.exists():
            import shutil
            shutil.copy(best_ckpt, output_dir / f"best-{args.kind}.pt")
    if world_size > 1:
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
