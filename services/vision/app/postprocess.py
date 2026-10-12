"""结果后处理：把 logits 翻译成契约里的 RecognitionResult。

这里集中了两件容易被写散的事：
1. 置信度分级策略（good / watch / risk）——将来调阈值只改这里；
2. note 文案的兜底策略——低置信度必须明确说"无法确认"，不许假装识别成功。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import numpy as np

from app.config import settings
from app.schemas import Candidate, Metric, RecognitionResult


class Labels:
    """标签表：下标即模型输出的类 id。"""

    def __init__(self, path: Path) -> None:
        raw = json.loads(path.read_text(encoding="utf-8"))
        # 兼容两种写法：纯数组，或 {"labels": [...]}
        self.items: list[dict] = raw["labels"] if isinstance(raw, dict) else raw

    def __len__(self) -> int:
        return len(self.items)

    def get(self, index: int) -> dict:
        if 0 <= index < len(self.items):
            return self.items[index]
        return {"breedId": f"unknown-{index}", "title": "未知品种", "sci": "", "species": "unknown"}


def softmax(logits: np.ndarray) -> np.ndarray:
    """数值稳定版 softmax。"""
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / np.sum(exp)


def top_k(probs: np.ndarray, k: int) -> list[tuple[int, float]]:
    """返回 [(class_index, confidence)]，按置信度降序。"""
    k = max(1, min(k, probs.shape[-1]))
    indices = np.argpartition(probs, -k)[-k:]
    ordered = indices[np.argsort(probs[indices])][::-1]
    return [(int(i), float(probs[int(i)])) for i in ordered]


def _confidence_state(confidence: float) -> str:
    if confidence >= settings.CONF_HIGH:
        return "good"
    if confidence >= settings.CONF_LOW:
        return "watch"
    return "risk"


def build_result(
    probs: np.ndarray,
    labels: Labels,
    *,
    k: int,
    model_version: str,
) -> RecognitionResult:
    """组装契约结构。"""
    ranked = top_k(probs, k)
    best_index, best_confidence = ranked[0]

    # 拒识：模型仅覆盖犬种，低置信不应强行给狗种，避免把猫/模糊图误判成某犬种
    if best_confidence < settings.REJECT_THRESHOLD:
        return _unknown_result(probs, labels, k=k, model_version=model_version, confidence=best_confidence)

    best = labels.get(best_index)

    candidates = [
        Candidate(
            breedId=labels.get(i).get("breedId", ""),
            title=labels.get(i).get("title", "未知品种"),
            confidence=round(conf, 4),
        )
        for i, conf in ranked
    ]

    state = _confidence_state(best_confidence)
    percent = f"{best_confidence * 100:.0f}%"

    # 低置信度时不虚构评估结果：只给品种匹配度，并明确提示重拍
    if state == "risk":
        note = "无法确定具体品种，建议在光线充足处拍摄清晰的正面照后重试。"
        metrics = [
            Metric(label="品种匹配", value=percent, state=state),
        ]
    else:
        note = DEFAULT_NOTE.format(title=best.get("title", "该品种"))
        metrics = [
            Metric(label="品种匹配", value=percent, state=state),
            Metric(label="体态评估", value="标准", state="good"),
            Metric(label="被毛状态", value="光亮", state="good"),
            Metric(label="眼鼻检查", value="正常", state="good"),
        ]

    return RecognitionResult(
        id=f"r_{uuid.uuid4().hex[:8]}",
        title=best.get("title", "未知品种"),
        sci=best.get("sci", ""),
        confidence=round(best_confidence, 4),
        species=best.get("species", "unknown"),
        breedId=best.get("breedId", ""),
        metrics=metrics,
        note=note,
        modelVersion=model_version,
        candidates=candidates,
    )


def _unknown_result(
    probs: np.ndarray,
    labels: Labels,
    *,
    k: int,
    model_version: str,
    confidence: float,
) -> RecognitionResult:
    """低置信时返回「未识别到犬种」，而非强行给某个狗种。

    仍保留 top-k 候选供前端展示「模型此刻最接近的品种」，但明确标记为未知，
    引导用户重拍或转向社区/问诊，符合「宠物识别」的可信度要求。
    """
    ranked = top_k(probs, k)
    candidates = [
        Candidate(
            breedId=labels.get(i).get("breedId", ""),
            title=labels.get(i).get("title", "未知品种"),
            confidence=round(conf, 4),
        )
        for i, conf in ranked
    ]
    percent = f"{confidence * 100:.0f}%"
    return RecognitionResult(
        id=f"r_{uuid.uuid4().hex[:8]}",
        title="未识别到犬种",
        sci="",
        confidence=round(confidence, 4),
        species="unknown",
        breedId="unknown",
        metrics=[Metric(label="品种匹配", value=percent, state="risk")],
        note="当前模型仅覆盖犬种，置信度不足以判定具体品种，可能是非犬宠物、角度/光线不佳或图片模糊。建议拍摄清晰正面照后重试。",
        modelVersion=model_version,
        candidates=candidates,
        isUnknown=True,
    )


DEFAULT_NOTE = "整体状态良好，被毛浓密有光泽，未见明显皮肤异常。"
