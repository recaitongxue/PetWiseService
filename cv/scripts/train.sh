#!/usr/bin/env bash
# 训练 / 评测入口。自动检测 GPU 数量，多卡时用 torchrun 启动 DDP（双 5090 并行）。
# 用法：
#   bash scripts/train.sh dog                 # 训练狗（默认 configs/train.yaml，自动 DDP）
#   bash scripts/train.sh cat                 # 训练猫
#   bash scripts/train.sh dog --only-eval    # 仅用已有权重评测测试集
#   bash scripts/train.sh dog --resume artifacts/artifacts/best-checkpoint.pt
#   NPROC=1 bash scripts/train.sh dog        # 强制单卡
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"

KIND="${1:-dog}"
CONFIG="${2:-$KIND/configs/train.yaml}"
shift 2 2>/dev/null || true

NPROC="${NPROC:-$(python -c "import torch;print(int(torch.cuda.device_count()))" 2>/dev/null || echo 1)}"
if [ "$NPROC" -ge 2 ]; then
  echo "[train.sh] 检测到 ${NPROC} 张 GPU，使用 torchrun DDP"
  torchrun --nproc_per_node="$NPROC" -m common.train.cli --kind "$KIND" --config "$CONFIG" "$@"
else
  echo "[train.sh] 单卡模式"
  python -m common.train.cli --kind "$KIND" --config "$CONFIG" "$@"
fi
