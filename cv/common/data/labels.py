"""标签映射：从数据集派生 类别索引 <-> 名称，并持久化为 labels-<kind>.json。

- 狗 (THU-Dogs)：类别来自 TrainAndValList/train.lst 的首级目录（品种目录），
  显示名去掉形如 "1043-n000001-" 的前缀，仅保留品种名（如 Shiba_Dog）。
- 猫：类别来自 train/ 下的子目录名。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

_DOG_LST_RE = re.compile(r"^\s*\.+/+(.+?)/(.+)$")
_NAME_RE = re.compile(r"^\d+-n\d+-(.+)$")


def _dog_breed_dirs(train_lst: Path) -> list[str]:
    """从 train.lst 解析所有品种目录名（去重、排序）。"""
    dirs: set[str] = set()
    with train_lst.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = _DOG_LST_RE.match(line)
            if m:
                dirs.add(m.group(1))
    return sorted(dirs)


def _cat_breed_dirs(train_root: Path) -> list[str]:
    return sorted(p.name for p in train_root.iterdir() if p.is_dir())


def _display_name(folder: str) -> str:
    m = _NAME_RE.match(folder)
    return m.group(1) if m else folder


def build_labels(kind: str, root: str | Path, artifacts_dir: str | Path) -> dict:
    """构建并保存标签映射，返回 {"kind","folders","names","folder_to_idx"}。"""
    root = Path(root)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if kind == "dog":
        train_lst = root / "TrainAndValList" / "train.lst"
        folders = _dog_breed_dirs(train_lst)
    elif kind == "cat":
        folders = _cat_breed_dirs(root / "train")
    else:
        raise ValueError(f"未知 kind={kind}")

    folders = sorted(folders)
    names = [_display_name(f) for f in folders]
    folder_to_idx = {f: i for i, f in enumerate(folders)}

    payload = {
        "kind": kind,
        "num_classes": len(folders),
        "folders": folders,
        "names": names,
        "folder_to_idx": folder_to_idx,
    }
    out = artifacts_dir / f"labels-{kind}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_labels(kind: str, artifacts_dir: str | Path) -> dict:
    path = Path(artifacts_dir) / f"labels-{kind}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"未找到 {path}，请先运行 prepare.sh 生成 labels-{kind}.json"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_dataset_yaml(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
