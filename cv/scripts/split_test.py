#!/usr/bin/env python
"""将 THU-Dogs 的 validation.lst 确定性切分为 val.lst + test.lst。

为什么要切
----------
官方 THU-Dogs 只发 train + validation，没有 test。若把 validation 同时用来
「早停选模型」和「最终报指标」，上报数字会偏乐观（验证集参与了模型选择）。
最干净的补救：把 validation.lst 按**每类**确定性切分（默认各 20/类），
- val.lst  → 训练期早停 / 选模型
- test.lst → 训练全程不碰，最终评测才用，指标才可信

特性
----
- 不修改 train.lst；保留原始 validation.lst 供回退/兼容。
- 按品种分组后，在固定 seed 下打乱并切分，相同参数永远得到相同结果。
- 可复现：配合 dataset.yaml 的 seed，保证切分与训练都可重跑。
- 幂等：val.lst / test.lst 已存在且未加 --force 时直接跳过。
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path


def _breed_of(line: str) -> str:
    """从 lst 一行里取出品种文件夹名（先去掉 BOM / `.//` 前缀）。"""
    rel = line.strip().lstrip("\ufeff").lstrip(".").lstrip("/").strip()
    return rel.split("/", 1)[0] if "/" in rel else rel


def main() -> None:
    p = argparse.ArgumentParser(description="切分 THU-Dogs 测试集")
    p.add_argument("--root", type=Path, default=Path("datasets"), help="数据集根目录")
    p.add_argument("--src", type=Path, default=None, help="源 lst（默认 <root>/TrainAndValList/validation.lst）")
    p.add_argument("--out-dir", type=Path, default=None, help="输出目录（默认同 src 所在目录）")
    p.add_argument("--ratio", type=float, default=0.5, help="val 占比，剩余归 test")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--force", action="store_true", help="覆盖已存在的 val.lst / test.lst")
    a = p.parse_args()

    root = Path(a.root)
    src = a.src or (root / "TrainAndValList" / "validation.lst")
    out_dir = a.out_dir or src.parent
    val_path = out_dir / "val.lst"
    test_path = out_dir / "test.lst"

    if val_path.is_file() and test_path.is_file() and not a.force:
        print(f"[split] 已存在 val.lst/test.lst，跳过（用 --force 覆盖）")
        return
    if not src.is_file():
        raise SystemExit(f"找不到源划分文件: {src}")

    raw = src.read_text(encoding="utf-8-sig").splitlines()
    lines = [ln for ln in raw if ln.strip()]

    groups: dict[str, list[str]] = {}
    for ln in lines:
        groups.setdefault(_breed_of(ln), []).append(ln)

    val_lines: list[str] = []
    test_lines: list[str] = []
    rng = random.Random(a.seed)
    for breed in sorted(groups):
        items = sorted(groups[breed])      # 先排序保证原始顺序确定
        rng.shuffle(items)                 # 固定 seed 下打乱，可复现
        n = len(items)
        n_val = max(1, round(n * a.ratio))
        if n > 1:
            n_val = min(n_val, n - 1)      # 至少留 1 张给 test
        val_lines.extend(items[:n_val])
        test_lines.extend(items[n_val:])

    out_dir.mkdir(parents=True, exist_ok=True)
    val_path.write_text("\n".join(val_lines) + "\n", encoding="utf-8")
    test_path.write_text("\n".join(test_lines) + "\n", encoding="utf-8")
    print(
        f"[split] 共 {len(groups)} 类 | val.lst={len(val_lines)} 行 | "
        f"test.lst={len(test_lines)} 行 | seed={a.seed}"
    )


if __name__ == "__main__":
    main()
