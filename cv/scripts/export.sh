#!/usr/bin/env bash
# 导出 ONNX：把 artifacts/best.pt 转成 services/vision 可直接加载的权重 + 清单
set -euo pipefail
cd "$(dirname "$0")/.."

: "${KIND:=dog}"
: "${VERSION:=v1}"

python -m src.export.to_onnx \
  --checkpoint "${CKPT:-artifacts/best.pt}" \
  --labels "${LABELS:-artifacts/labels.json}" \
  --kind "$KIND" \
  --version "$VERSION" \
  --image-size "${IMAGE_SIZE:-224}" \
  ${QUANTIZE:+--quantize}
