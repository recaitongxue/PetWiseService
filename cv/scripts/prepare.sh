#!/usr/bin/env bash
# 数据准备（只需 CPU）：
#   1) 切分测试集：把 validation.lst 确定性切成 val.lst（早停/选模型）+ test.lst（独立评测）
#   2) 生成 labels.json：解析全部 lst，产出类别表
# 数据根目录默认读 configs/dataset.yaml 的 dataset.root；设 ROOT_DIR 可覆盖（Docker 挂载等）
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/split_test.py \
  --root "${ROOT_DIR:-datasets}" \
  --ratio "${TEST_RATIO:-0.5}" \
  --seed "${SEED:-42}"

python -m src.data.make_labels \
  --dataset-config configs/dataset.yaml \
  ${ROOT_DIR:+--root "$ROOT_DIR"} \
  --out "${OUT:-artifacts/labels.json}" \
  --version "${VERSION:-v1}"
