#!/usr/bin/env bash
# 生成标签映射 labels-<kind>.json（训练必需，类别索引<->名称）
# 用法：bash scripts/prepare.sh [dog] [cat]
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

KINDS=("$@")
if [ ${#KINDS[@]} -eq 0 ]; then KINDS=(dog cat); fi

for KIND in "${KINDS[@]}"; do
  echo "==> 构建 ${KIND} 标签映射"
  python -c "
import sys; sys.path.insert(0,'.')
from common.data.labels import build_labels
kind='${KIND}'
root='datasets/'+kind
out='artifacts/artifacts'
import os; os.makedirs(out, exist_ok=True)
labels=build_labels(kind, root, out)
print(f'  {kind}: {labels[\"num_classes\"]} 类 -> artifacts/artifacts/labels-{kind}.json')
"
done
