"""导出 ONNX：加载训练得到的最佳权重，导出为动态 batch 的 ONNX 模型。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from common.data import labels as labels_mod  # noqa: E402
from common.models import factory as model_factory  # noqa: E402


def export_onnx(kind: str, weights: Path, out_path: Path, image_size: int, num_classes: int, backbone: str):
    model = model_factory.build_model(backbone, num_classes, pretrained=False)
    sd = torch.load(weights, map_location="cpu")
    model.load_state_dict(sd.get("state_dict", sd), strict=False)
    model.eval()
    dummy = torch.randn(1, 3, image_size, image_size)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        dummy,
        out_path,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"[export] 已导出 ONNX -> {out_path}  ({out_path.stat().st_size/1e6:.1f} MB)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=["dog", "cat"])
    p.add_argument("--weights", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--artifacts", type=Path, default=ROOT / "artifacts" / "artifacts")
    p.add_argument("--config", type=Path, default=None)
    args = p.parse_args()

    artifacts = Path(args.artifacts)
    labels = labels_mod.load_labels(args.kind, artifacts)
    num_classes = len(labels["names"])
    cfg = labels_mod.load_dataset_yaml(args.config or (ROOT / args.kind / "configs" / "train.yaml"))
    ds = labels_mod.load_dataset_yaml(ROOT / args.kind / "configs" / "dataset.yaml")
    image_size = int(ds["dataset"]["image_size"])
    backbone = cfg["backbone"]
    weights = args.weights or (artifacts / f"best-{args.kind}.pt")
    out = args.out or (artifacts / f"{args.kind}.onnx")
    export_onnx(args.kind, weights, out, image_size, num_classes, backbone)


if __name__ == "__main__":
    main()
