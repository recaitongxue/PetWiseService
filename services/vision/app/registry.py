"""模型注册表。

职责：把「磁盘上的 artifacts」翻译成「可按 kind 选择的模型条目」。

为什么要这一层：
- cv/ 导出的可能不止一个模型（犬种、猫种、皮肤病），按 kind 路由避免一次性全部加载；
- 版本号三方对齐（artifacts/manifest.json ↔ engine ↔ 契约 RecognitionResult.modelVersion）；
- 缺贬权重时给出可读的错误，而不是让服务以半死状态启动。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

_UNSET_VERSION = "unversioned"


@dataclass(frozen=True)
class ModelEntry:
    """单个模型条目。"""

    kind: str                 # dog | cat | skin ...
    version: str
    onnx_path: Path
    labels_path: Path
    image_size: int
    mean: tuple[float, float, float]
    std: tuple[float, float, float]

    @property
    def exists(self) -> bool:
        return self.onnx_path.is_file() and self.labels_path.is_file()


class ModelRegistry:
    """从 manifest.json 加载模型清单，惰性按需创建会话。"""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self.artifacts_dir = artifacts_dir or settings.ARTIFACTS_DIR
        self._entries: dict[str, ModelEntry] = {}
        self._load_error: str | None = None
        self.reload()

    # ── 加载 ─────────────────────────────────────────────────
    def reload(self) -> None:
        manifest_path = self.artifacts_dir / settings.MANIFEST_FILE
        if not manifest_path.is_file():
            self._load_error = (
                f"未找到 {manifest_path}；请先在 cv/ 执行 python -m src.export.to_onnx 导出权重与清单"
            )
            self._entries = {}
            return

        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries: dict[str, ModelEntry] = {}
        for item in raw.get("models", []):
            entry = ModelEntry(
                kind=item["kind"],
                version=item.get("version", _UNSET_VERSION),
                onnx_path=self.artifacts_dir / item["onnx"],
                labels_path=self.artifacts_dir / item["labels"],
                image_size=int(item.get("imageSize", settings.IMAGE_SIZE)),
                mean=tuple(item.get("mean", (0.485, 0.456, 0.406))),  # type: ignore[arg-type]
                std=tuple(item.get("std", (0.229, 0.224, 0.225))),  # type: ignore[arg-type]
            )
            entries[entry.kind] = entry

        self._entries = entries
        self._load_error = None

    # ── 查询 ─────────────────────────────────────────────────
    @property
    def load_error(self) -> str | None:
        return self._load_error

    @property
    def kinds(self) -> list[str]:
        return sorted(self._entries)

    def entry_for(self, kind: str) -> ModelEntry:
        """按 kind 取条目；kind=auto 时退化为唯一模型。"""
        if kind != "auto" and kind in self._entries:
            return self._entries[kind]

        if len(self._entries) == 1:
            return next(iter(self._entries.values()))

        raise KeyError(
            f"kind={kind} 无对应模型（已注册: {', '.join(self.kinds) or '空'}）"
        )
