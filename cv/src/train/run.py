"""训练入口（可直接在 GPU 服务器上跑）。

    python -m src.train.run --config configs/train.yaml

流程：生成 labels.json → 构建数据集 → 构建模型 → 训练（含早停 / 断点续训）
→ 在验证集上评测（top-1 / top-5 / 各类召回）→ 写出报告。

数据根目录等全部参数优先读 configs/dataset.yaml；命令行 --root 可覆盖（便于 Docker 挂载）。
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader

from src.data.thudogs import build_loaders, make_labels
from src.eval.evaluate import evaluate, save_report
from src.models.factory import SUPPORTED_BACKBONES, build_model
from src.train.trainer import TrainConfig, Trainer


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="训练狗品种识别模型")
    parser.add_argument("--config", type=Path, default=Path("configs/train.yaml"))
    parser.add_argument("--dataset-config", type=Path, default=Path("configs/dataset.yaml"))
    # 数据根目录优先取 dataset.yaml 的 dataset.root；命令行 --root 仅用于覆盖（Docker 挂载等）
    parser.add_argument("--root", type=Path, default=None, help="覆盖 configs/dataset.yaml 的 dataset.root")
    parser.add_argument("--resume", type=Path, default=None, help="断点续训的 checkpoint")
    parser.add_argument("--only-eval", action="store_true", help="只评测已有 best.pt，不训练")
    parser.add_argument("--version", default="v1", help="labels.json 版本号")
    args = parser.parse_args()

    cfg = _load_yaml(args.config)
    ds = _load_yaml(args.dataset_config)

    # 数据根目录：yaml 优先，命令行覆盖
    root = Path(args.root) if args.root else Path(ds["dataset"].get("root", "datasets"))
    whitelist = ds["dataset"].get("classes") or None  # 非空则只训白名单内的品种（MVP）

    # 固定随机种子，保证可复现（影响类平衡采样等）
    seed = int(ds["dataset"].get("seed", 42))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    print(f"[init] 数据根目录 = {root}  seed = {seed}")

    # 1) 标签表（类别下标与训练强一致）
    cn_path = Path(__file__).resolve().parent.parent / "data" / "breed_cn.json"
    labels = make_labels(
        root,
        out_path=Path(cfg["output"]["dir"]) / "labels.json",
        version=args.version,
        image_size=ds["dataset"]["image_size"],
        cn_map=json.loads(cn_path.read_text(encoding="utf-8")) if cn_path.is_file() else None,
        whitelist=whitelist,
    )
    num_classes = len(labels)
    print(f"[init] 类别数 = {num_classes}" + (f"（白名单 {len(whitelist)} 类）" if whitelist else ""))

    # 配置里的 num_classes 仅作校验，避免数据集变动后静默训错维度
    mcfg = cfg["model"]
    if "num_classes" in mcfg and mcfg["num_classes"] != num_classes:
        raise SystemExit(f"配置 num_classes={mcfg['num_classes']} 与数据集实际 {num_classes} 不符")

    # 2) 数据集（train / val / test 三路；test 由 prepare 阶段切分生成）
    train_loader, val_loader, test_loader, classes = build_loaders(
        root,
        image_size=ds["dataset"]["image_size"],
        batch_size=ds["dataloader"]["batch_size"],
        num_workers=ds["dataloader"]["num_workers"],
        use_bbox=ds["dataset"].get("use_bbox", True),
        balanced=ds["dataset"].get("balanced_sampling", True),
        whitelist=whitelist,
        seed=seed,
        test_split=ds["dataset"].get("test_split", True),
    )
    print(f"[init] train={len(train_loader.dataset)}  val={len(val_loader.dataset)}  "
          f"test={len(test_loader.dataset) if test_loader else 0}  "
          f"use_bbox={ds['dataset'].get('use_bbox', True)}  "
          f"balanced={ds['dataset'].get('balanced_sampling', True)}")

    # 3) 模型
    mcfg = cfg["model"]
    if mcfg["backbone"] not in SUPPORTED_BACKBONES:
        raise SystemExit(f"不支持的骨干: {mcfg['backbone']}，可选 {SUPPORTED_BACKBONES}")
    model = build_model(num_classes, backbone=mcfg["backbone"], pretrained=mcfg["pretrained"])

    # 4) 训练 / 评测
    tcfg = TrainConfig(
        epochs=mcfg["epochs"],
        lr=mcfg["lr"],
        weight_decay=mcfg["weight_decay"],
        patience=mcfg["patience"],
        amp=mcfg["amp"],
        num_classes=num_classes,
        backbone=mcfg["backbone"],
        label_smoothing=mcfg.get("label_smoothing", 0.05),
        mixup=mcfg.get("mixup", 0.0),
        cutmix=mcfg.get("cutmix", 0.0),
        output_dir=Path(cfg["output"]["dir"]),
    )

    if not args.only_eval:
        trainer = Trainer(model, tcfg, resume_from=args.resume)
        report = trainer.fit(train_loader, val_loader)
        print(f"[train] 最优 top-1 = {report['bestTop1']:.4f}，耗时 {report['elapsedSec']}s")

    # 5) 评测（优先在独立测试集 test 上跑，指标才可信；无 test 时退回验证集）
    ckpt = Path(cfg["output"]["dir"]) / cfg["output"]["save_name"]
    state = torch.load(ckpt, map_location="cpu")
    model.load_state_dict(state.get("state_dict", state))
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    eval_loader = test_loader if test_loader is not None else val_loader
    eval_split = "test" if test_loader is not None else "val"
    eval_report = evaluate(model, eval_loader)
    save_report(eval_report, Path(cfg["output"]["dir"]), class_names=classes, name=eval_split)
    print(f"[eval:{eval_split}] top-1={eval_report['top1']:.4f}  top-5={eval_report['top5']:.4f}")
    print(f"[eval:{eval_split}] 最易混淆: {eval_report['worstClasses'][:5]}")


if __name__ == "__main__":
    main()
