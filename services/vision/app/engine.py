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
        """启动时的预热：用一张纯色图跑一次，避免首个真实请求承担全部冷启动成本。

        kind=auto 且注册了多个模型时，依次预热每个 kind（否则 entry_for("auto") 会拒绝）。
        """
        kinds = self.registry.kinds if kind == "auto" else [kind]
        if not kinds:
            return False

        from PIL import Image

        ok = True
        for k in kinds:
            try:
                entry, _, _ = self._session_for(k)
                blank = Image.new("RGB", (entry.image_size, entry.image_size), (128, 128, 128))
            except Exception:  # noqa: BLE001
                return False
            try:
                import io

                buffer = io.BytesIO()
                blank.save(buffer, format="JPEG")
                self.predict(buffer.getvalue(), kind=k, top_k=1)
            except Exception:  # noqa: BLE001
                ok = False
        return ok

    # ── 推理 ─────────────────────────────────────────────────
    def predict(
        self,
        image_bytes: bytes,
        *,
        kind: str = "auto",
        top_k: int | None = None,
    ) -> RecognitionResult:
        if kind == "auto":
            # 多模型路由：狗/猫视觉差异大，取各模型 top-1 置信度最高的那个；
            # 若最高置信仍低于拒识阈值，对应模型自身已返回 isUnknown，直接透传。
            return self.route(image_bytes, top_k=top_k)

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

    # ── 物种路由 ─────────────────────────────────────────────
    def route(self, image_bytes: bytes, *, top_k: int | None = None) -> RecognitionResult:
        """kind=auto 且注册了多个模型时：逐模型推理，返回置信度最高的结果。

        狗/猫在视觉上极易区分，正确物种的模型会给出明显高于错误物种的置信度，
        因此「取最大置信」即可稳健路由；模糊/非宠物图则各模型都低置信，
        由对应模型自身返回 isUnknown 透传，不会强行认成某品种。
        """
        kinds = self.registry.kinds
        if not kinds:
            raise ModelNotReadyError("没有可用的模型")
        if len(kinds) == 1:
            return self.predict(image_bytes, kind=kinds[0], top_k=top_k)

        best: RecognitionResult | None = None
        best_conf = -1.0
        for k in kinds:
            try:
                res = self.predict(image_bytes, kind=k, top_k=top_k)
            except ModelNotReadyError:
                continue
            if res.confidence > best_conf:
                best_conf = res.confidence
                best = res
        if best is None:
            raise ModelNotReadyError("所有模型均不可用")
        return best
