"""推理引擎。

关键设计：
- **会话单例**：ONNX Session 创建一次并复用，绝不在请求里 new；
- **惰性加载**：按 kind 首次调用时才建会话，避免启动即加载全部模型；
- **依赖可选**：onnxruntime 缺失时服务仍可启动并返回明确降级，
  这样在没有装推理依赖的机器上跑冒烟测试不会直接崩。
"""

from __future__ import annotations

from threading import Lock
from typing import Any

import numpy as np

from app.config import settings
from app.postprocess import Labels, build_result, softmax
from app.preprocess import InvalidImageError, ImageTooLargeError, load_image, to_tensor
from app.registry import ModelEntry, ModelRegistry
from app.schemas import RecognitionResult


class ModelNotReadyError(RuntimeError):
    pass


class InferenceEngine:
    """线程安全的 ONNX 会话持有者。"""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()
        self._sessions: dict[str, Any] = {}
        self._labels: dict[str, Labels] = {}
        self._lock = Lock()
        self._providers = self._resolve_providers()

    # ── 提供者 ───────────────────────────────────────────────
    @staticmethod
    def _resolve_providers() -> list[str]:
        """决定用 CPU 还是 CUDA；auto 模式优先显存。"""
        mode = settings.PROVIDERS.lower()
        if mode == "cpu":
            return ["CPUExecutionProvider"]
        try:
            import onnxruntime as ort  # noqa: PLC0415

            available = ort.get_available_providers()
        except ImportError:
            return ["CPUExecutionProvider"]

        if mode == "cuda" or "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    @property
    def provider(self) -> str:
        return "cuda" if self._providers[0].startswith("CUDA") else "cpu"

    # ── 会话管理 ─────────────────────────────────────────────
    def _session_for(self, kind: str) -> tuple[ModelEntry, Any, Labels]:
        entry = self.registry.entry_for(kind)
        if not entry.exists:
            raise ModelNotReadyError(
                f"模型文件缺失: {entry.onnx_path.name} / {entry.labels_path.name}"
            )

        key = f"{entry.kind}:{entry.version}"
        with self._lock:
            if key not in self._sessions:
                import onnxruntime as ort  # 惰性导入：缺依赖时不影响其它端点

                session = ort.InferenceSession(
                    str(entry.onnx_path), providers=self._providers
                )
                self._sessions[key] = session
                self._labels[key] = Labels(entry.labels_path)
            return entry, self._sessions[key], self._labels[key]

    def warmup(self, kind: str = "auto") -> bool:
        """启动时的预热：用一张纯色图跑一次，避免首个真实请求承担全部冷启动成本。"""
        try:
            from PIL import Image

            entry, _, _ = self._session_for(kind)
            blank = Image.new("RGB", (entry.image_size, entry.image_size), (128, 128, 128))
        except Exception:  # noqa: BLE001 - 预热失败不应阻断启动
            return False

        try:
            import io

            buffer = io.BytesIO()
            blank.save(buffer, format="JPEG")
            self.predict(buffer.getvalue(), kind=kind, top_k=1)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ── 推理 ─────────────────────────────────────────────────
    def predict(
        self,
        image_bytes: bytes,
        *,
        kind: str = "auto",
        top_k: int | None = None,
    ) -> RecognitionResult:
        entry, session, labels = self._session_for(kind)

        try:
            image = load_image(image_bytes)
        except ImageTooLargeError as exc:
            raise ValueError(str(exc)) from exc
        except InvalidImageError as exc:
            raise ValueError(str(exc)) from exc

        tensor = to_tensor(
            image,
            image_size=entry.image_size,
            mean=entry.mean,
            std=entry.std,
        )

        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: tensor})
        logits = np.asarray(outputs[0]).reshape(-1)

        # 有些导出没有 softmax，这里统一处理
        probs = logits if abs(float(np.sum(logits)) - 1.0) < 1e-3 else softmax(logits)

        return build_result(
            probs,
            labels,
            k=top_k or settings.TOP_K,
            model_version=entry.version,
        )

    @property
    def loaded_models(self) -> list[str]:
        return sorted({key.split(":")[0] for key in self._sessions})
