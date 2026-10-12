"""把训练产物导出为推理服务可直接加载的形态。

这是**离线层与在线层唯一的交接点**，产出三样东西：

    artifacts/model-<kind>-<version>.onnx    推理图
    artifacts/labels-<kind>.json             类别清单（下标即类 id）
    artifacts/manifest.json                  推理服务的模型注册表

推理服务只读这三样，不需要知道训练时用了什么框架。
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"

_NORM_MEAN = [0.485, 0.456, 0.406]
_NORM_STD = [0.229, 0.224, 0.225]


def export_model(
    checkpoint: Path,
    labels: Path,
    *,
    kind: str,
    version: str,
    image_size: int = 224,
    num_classes: int | None = None,
    quantize: bool = False,
    artifacts_dir: Path = ARTIFACTS_DIR,
) -> dict:
    """导出单个模型并更新 manifest.json。"""
    import torch
    # 以 `python -m src.export.to_onnx` 方式运行时，用绝对包路径导入
    from src.models.factory import SUPPORTED_BACKBONES, build_model

    labels_data = json.loads(labels.read_text(encoding="utf-8"))
    label_list = labels_data["labels"] if isinstance(labels_data, dict) else labels_data
    class_count = num_classes or len(label_list)

    state = torch.load(checkpoint, map_location="cpu")
    backbone = state.get("backbone") or "resnet50"
    if backbone not in SUPPORTED_BACKBONES:
        backbone = "resnet50"
    model = build_model(class_count, backbone=backbone, pretrained=False)
    model.load_state_dict(state.get("state_dict", state))
    model.eval()

    dummy = torch.randn(1, 3, image_size, image_size)
    onnx_name = f"model-{kind}-{version}{'-int8' if quantize else ''}.onnx"
    labels_name = f"labels-{kind}.json"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = artifacts_dir / onnx_name

    torch.onnx.export(
        model,
        dummy,
        str(onnx_path),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}},
        opset_version=13,
    )

    if quantize:  # 体积与延迟都能再降一档，精度损失通常可接受
        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantized = artifacts_dir / f"model-{kind}-{version}-int8.onnx"
        quantize_dynamic(str(onnx_path), str(quantized), weight_type=QuantType.QUInt8)
        onnx_path = quantized

    (artifacts_dir / labels_name).write_text(
        json.dumps(labels_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _update_manifest(
        artifacts_dir,
        kind=kind,
        version=version,
        onnx=onnx_path.name,
        labels=labels_name,
        image_size=image_size,
    )

    size_mb = onnx_path.stat().st_size / 1024 / 1024
    print(f"[export] {onnx_path.name} 导出完成，{size_mb:.1f}MB")
    return {"onnx": str(onnx_path), "sizeMb": round(size_mb, 2)}


def _update_manifest(
    artifacts_dir: Path,
    *,
    kind: str,
    version: str,
    onnx: str,
    labels: str,
    image_size: int,
) -> None:
    """合并写入 manifest.json：同 kind 覆盖，其它保留。"""
    manifest_path = artifacts_dir / "manifest.json"
    manifest = {"models": []}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    entry = {
        "kind": kind,
        "version": version,
        "onnx": onnx,
        "labels": labels,
        "imageSize": image_size,
        "mean": _NORM_MEAN,
        "std": _NORM_STD,
        "exportedAt": int(time.time()),
    }
    models = [m for m in manifest.get("models", []) if m.get("kind") != kind]
    models.append(entry)
    manifest["models"] = sorted(models, key=lambda m: m["kind"])

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[export] manifest 已更新，当前 {len(models)} 个模型")


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 ONNX 权重与模型清单")
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--kind", default="dog", help="dog | cat | skin")
    parser.add_argument("--version", default="v1", help="如 v1")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--quantize", action="store_true")
    args = parser.parse_args()

    export_model(
        args.checkpoint,
        args.labels,
        kind=args.kind,
        version=args.version,
        image_size=args.image_size,
        quantize=args.quantize,
    )


if __name__ == "__main__":
    main()
