#!/usr/bin/env bash
# 导出 ONNX（动态 batch），供线上推理服务使用
# 用法：bash scripts/export.sh dog   |   bash scripts/export.sh cat
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

KIND="${1:-dog}"
echo "==> 导出 ${KIND} ONNX"
python -m common.export.to_onnx --kind "$KIND"
