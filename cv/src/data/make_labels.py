"""生成推理侧所需的 labels.json（只需 CPU，秒级完成）。

类别下标 = THU-Dogs 按文件夹名排序后的位置，与训练时 class_to_idx 严格一致。
可与训练解耦，单独跑：python -m src.data.make_labels
数据根目录优先读 configs/dataset.yaml 的 dataset.root；命令行 --root 可覆盖。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from src.data.thudogs_meta import make_labels

_HERE = Path(__file__).resolve().parent
_DEFAULT_CN = _HERE / "breed_cn.json"
_DEFAULT_DS_CFG = _HERE.parent.parent / "configs" / "dataset.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 dog 标签表 labels.json")
    parser.add_argument("--dataset-config", type=Path, default=_DEFAULT_DS_CFG, help="读 dataset.root")
    parser.add_argument("--root", type=Path, default=None, help="覆盖 dataset.yaml 的 dataset.root")
    parser.add_argument("--out", type=Path, default=Path("artifacts/labels.json"))
    parser.add_argument("--version", default="v1")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--cn", type=Path, default=_DEFAULT_CN, help="中文名映射（可选）")
    args = parser.parse_args()

    # 根目录 / image_size：yaml 优先，命令行覆盖
    cfg = {}
    if args.dataset_config.is_file():
        cfg = yaml.safe_load(args.dataset_config.read_text(encoding="utf-8")) or {}
    ds_cfg = cfg.get("dataset", {})
    root = Path(args.root) if args.root else Path(ds_cfg.get("root", "datasets"))
    image_size = int(args.image_size) if args.image_size != 224 else int(ds_cfg.get("image_size", args.image_size))

    cn_map = None
    if args.cn.is_file():
        cn_map = json.loads(args.cn.read_text(encoding="utf-8"))

    labels = make_labels(
        root,
        out_path=args.out,
        version=args.version,
        image_size=args.image_size,
        cn_map=cn_map,
    )
    print(f"[labels] 写入 {args.out}（{len(labels)} 类，版本 {args.version}，根目录 {root}）")
    print(f"[labels] 示例: {labels[0]}")


if __name__ == "__main__":
    main()
