"""论文级评测：Top-1/5、宏/微/加权 P-R-F1、平衡准确率、Cohen κ、ROC-AUC(OvR)、
头/中/尾分段精度、逐类召回、混淆矩阵（CSV+PNG）。"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader


def _unwrap(model):
    return model.module if hasattr(model, "module") else model


@torch.no_grad()
def _collect(model, loader: DataLoader, tta: bool, device):
    model = _unwrap(model).to(device)
    model.eval()
    y_true, y_pred, y_score = [], [], []
    for imgs, targets in loader:
        imgs = imgs.to(device, non_blocking=True)
        logits = model(imgs)
        if tta:
            logits_f = model(torch.flip(imgs, dims=[-1]))
            logits = (logits + logits_f) / 2.0
        probs = F.softmax(logits, dim=1)
        pred = logits.argmax(1)
        y_true.extend(targets.numpy().tolist())
        y_pred.extend(pred.cpu().numpy().tolist())
        y_score.append(probs.cpu().numpy())
    return np.array(y_true), np.array(y_pred), np.vstack(y_score)


def evaluate_full(
    model,
    loader: DataLoader,
    *,
    tta: bool = True,
    class_names: list[str] | None = None,
    train_counts: list[int] | None = None,
    output_dir: str | Path = ".",
    split: str = "test",
    kind: str = "dog",
) -> dict:
    device = next(model.parameters()).device
    y_true, y_pred, y_score = _collect(model, loader, tta, device)
    num_classes = y_score.shape[1]
    labels = list(range(num_classes))
    names = class_names if class_names else [str(i) for i in labels]

    report: dict = {"kind": kind, "split": split, "tta": tta, "numClasses": num_classes}

    # 基础指标
    top1 = float((y_pred == y_true).mean())
    top5 = float((y_score.argsort(1)[:, -5:] == y_true[:, None]).any(1).mean())
    report["top1"] = round(top1, 4)
    report["top5"] = round(top5, 4)

    # sklearn 指标
    try:
        from sklearn.metrics import (
            accuracy_score, balanced_accuracy_score, cohen_kappa_score,
            confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
        )
        report["precision"] = {
            "macro": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "micro": round(float(precision_score(y_true, y_pred, average="micro", zero_division=0)), 4),
            "weighted": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        }
        report["recall"] = {
            "macro": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "micro": round(float(recall_score(y_true, y_pred, average="micro", zero_division=0)), 4),
            "weighted": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        }
        report["f1"] = {
            "macro": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
            "micro": round(float(f1_score(y_true, y_pred, average="micro", zero_division=0)), 4),
            "weighted": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        }
        report["balancedAccuracy"] = round(float(balanced_accuracy_score(y_true, y_pred)), 4)
        report["cohenKappa"] = round(float(cohen_kappa_score(y_true, y_pred)), 4)
        try:
            report["rocAucMacroOvR"] = round(
                float(roc_auc_score(y_true, y_score, multi_class="ovr", average="macro")), 4
            )
        except Exception:
            report["rocAucMacroOvR"] = None
        report["accuracy"] = round(float(accuracy_score(y_true, y_pred)), 4)
    except Exception as exc:  # noqa: BLE001
        report["sklearnNote"] = f"sklearn 指标跳过: {exc}"

    # 头/中/尾分段精度（按训练样本数三分位）
    if train_counts and len(train_counts) == num_classes:
        order = np.argsort(train_counts)[::-1]
        n = len(order)
        head = set(order[: n // 3].tolist())
        mid = set(order[n // 3: 2 * n // 3].tolist())
        tail = set(order[2 * n // 3:].tolist())
        seg = {}
        for name, group in (("head", head), ("mid", mid), ("tail", tail)):
            idx = [i for i, t in enumerate(y_true) if t in group]
            seg[name] = round(float((y_pred[idx] == y_true[idx]).mean()), 4) if idx else None
        report["segmentAccuracy"] = seg

    # 逐类召回（暴露长尾 0% 类）
    per_class_recall = {}
    for c in labels:
        idx = np.where(y_true == c)[0]
        if len(idx) == 0:
            per_class_recall[names[c]] = None
        else:
            per_class_recall[names[c]] = round(float((y_pred[idx] == y_true[idx]).mean()), 4)
    report["perClassRecall"] = per_class_recall
    zero_recall = [names[c] for c in labels if per_class_recall.get(names[c], 1) == 0.0]
    report["zeroRecallClasses"] = zero_recall

    # 写文件
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"eval-report-{kind}-{split}-full"
    (out / f"{stem}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(out / f"{stem}.md", report, names)
    _save_confusion(out, y_true, y_pred, num_classes, names)

    return report


def _write_markdown(path: Path, report: dict, names: list[str]):
    lines = [f"# 评测报告（{report['kind']} / {report['split']}）", ""]
    lines.append(f"- TTA: {report['tta']}　样本类别数: {report['numClasses']}")
    lines.append("")
    lines.append("## 核心指标")
    lines.append(f"- Top-1: **{report['top1']}**　Top-5: **{report['top5']}**")
    for k in ("accuracy", "balancedAccuracy", "cohenKappa", "rocAucMacroOvR"):
        if k in report and report[k] is not None:
            lines.append(f"- {k}: {report[k]}")
    if "precision" in report:
        lines.append("")
        lines.append("| 粒度 | Precision | Recall | F1 |")
        lines.append("|---|---|---|---|")
        for g in ("macro", "micro", "weighted"):
            lines.append(f"| {g} | {report['precision'][g]} | {report['recall'][g]} | {report['f1'][g]} |")
    if "segmentAccuracy" in report:
        seg = report["segmentAccuracy"]
        lines.append("")
        lines.append(f"- 头部/中部/尾部类精度: {seg.get('head')} / {seg.get('mid')} / {seg.get('tail')}")
    if report.get("zeroRecallClasses"):
        lines.append("")
        lines.append(f"## 0% 召回类别（{len(report['zeroRecallClasses'])} 个）")
        lines.append(", ".join(report["zeroRecallClasses"]))
    path.write_text("\n".join(lines), encoding="utf-8")


def _save_confusion(out: Path, y_true, y_pred, num_classes, names):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_true, y_pred, labels=list(range(num_classes)))
        # CSV
        import csv
        with open(out / "confusion_matrix.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["true\\pred"] + names)
            for i in range(num_classes):
                w.writerow([names[i]] + [int(cm[i, j]) for j in range(num_classes)])
        # PNG
        fig, ax = plt.subplots(figsize=(max(8, num_classes * 0.5), max(8, num_classes * 0.5)))
        ax.imshow(cm, cmap="Blues")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        ax.set_xticks(range(num_classes))
        ax.set_yticks(range(num_classes))
        ax.set_xticklabels(names, rotation=90, fontsize=6)
        ax.set_yticklabels(names, fontsize=6)
        fig.colorbar(cm := ax.images[0], ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(out / "confusion_matrix.png", dpi=120)
        plt.close(fig)
    except Exception as exc:  # noqa: BLE001
        (out / "confusion_matrix.note").write_text(f"混淆矩阵图跳过: {exc}", encoding="utf-8")
