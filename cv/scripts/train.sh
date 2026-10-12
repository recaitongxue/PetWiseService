#!/usr/bin/env bash
# 训练狗品种识别模型（在 GPU 服务器上跑）
# 用法：bash scripts/train.sh [--resume artifacts/best.pt] [--only-eval]
set -euo pipefail
cd "$(dirname "$0")/.."

python -m src.train.run \
  --config configs/train.yaml \
  --dataset-config configs/dataset.yaml \
  ${ROOT_DIR:+--root "$ROOT_DIR"} \
  --version "${VERSION:-v1}" \
  "$@"
