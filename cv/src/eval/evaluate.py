"""评测：生成可直接放进论文的表格与指标。

除了 top-1 / top-5，还额外输出**每个类别的召回率**，
这对"哪些品种容易认错"的分析很有价值——毕设答辩常被问到。
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader) -> dict:
    device = next(model.parameters()).device
    model.eval()

    top1_correct = top5_correct = 0
    total = 0
    per_class_correct: dict[int, int] = {}
    per_class_total: dict[int, int] = {}
    confusion: list[list[int]] = []

    for images, targets in loader:
        images, targets = images.to(device), targets.to(device)
        outputs = model(images)

        _, pred5 = outputs.topk(min(5, outputs.size(1)), dim=1)
        top5_correct += pred5.eq(targets.view(-1, 1)).sum().item()
        predictions = outputs.argmax(1)

        top1_correct += (predictions == targets).sum().item()
        total += targets.size(0)

        for target, prediction in zip(targets.tolist(), predictions.tolist(), strict=True):
            per_class_total[target] = per_class_total.get(target, 0) + 1
            per_class_correct[target] = per_class_correct.get(target, 0) + (
                1 if target == prediction else 0
            )
            confusion.append([target, prediction])

    per_class_recall = {
        cls: round(per_class_correct.get(cls, 0) / count, 4)
        for cls, count in sorted(per_class_total.items())
    }

    return {
        "top1": round(top1_correct / max(1, total), 4),
        "top5": round(top5_correct / max(1, total), 4),
        "samples": total,
        "perClassRecall": per_class_recall,
        "worstClasses": sorted(per_class_recall.items(), key=lambda kv: kv[1])[:5],
        # 混淆明细保留在前 200 条，避免报告体积失控
        "confusionSample": confusion[:200],
    }


def render_markdown(report: dict, class_names: list[str] | None = None) -> str:
    """把评测结果渲染成 Markdown，便于直接粘进论文。"""
    lines = [
        "# 评测报告",
        "",
        f"- Top-1：{report['top1'] * 100:.2f}%",
        f"- Top-5：{report['top5'] * 100:.2f}%",
        f"- 样本数：{report['samples']}",
        "",
        "## 各类别召回率",
        "",
        "| 类别 | 召回率 |",
        "| --- | --- |",
    ]
    for cls, recall in report["perClassRecall"].items():
        name = class_names[int(cls)] if class_names and int(cls) < len(class_names) else str(cls)
        lines.append(f"| {name} | {recall * 100:.2f}% |")

    worst = ", ".join(
        (class_names[int(c)] if class_names and int(c) < len(class_names) else str(c))
        for c, _ in report["worstClasses"]
    )
    lines += ["", f"## 易混淆类别", "", worst or "无", ""]
    lines.append(f"报告生成时间：{json.dumps(report.get('generatedAt', ''), ensure_ascii=False)}")
    return "\n".join(lines)


def save_report(
    report: dict,
    output_dir: Path,
    class_names: list[str] | None = None,
    name: str = "val",
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"eval-report-{name}.json"
    md_path = output_dir / f"eval-report-{name}.md"
    # 记录本次评测用的是哪个划分，避免把 val / test 报告混在一起
    report = {**report, "split": name}
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report, class_names), encoding="utf-8")
    return md_path
