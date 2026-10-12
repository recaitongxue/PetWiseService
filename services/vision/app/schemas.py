"""输入输出数据结构。

字段口径严格对齐 packages/contracts/openapi.yaml 的 RecognitionResult，
不做任何"顺手加字段"的扩展，避免契约漂移。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Metric(BaseModel):
    """识别结果里的单项评估，state 决定前端配色。"""

    label: str
    value: str
    state: Literal["good", "watch", "risk"]


class Candidate(BaseModel):
    """候选品种。契约未定义该字段，但前端详情/纠错有用，作为可空扩展提供。"""

    breedId: str
    title: str
    confidence: float


class RecognitionResult(BaseModel):
    """GET/POST /recognitions 的 data 结构。"""

    id: str = Field(default="", description="识别记录 id，由 api 服务落库后回填")
    title: str
    sci: str = Field(default="", description="拉丁学名")
    confidence: float = Field(ge=0, le=1)
    species: str
    breedId: str
    metrics: list[Metric] = Field(default_factory=list)
    note: str = ""
    # 非契约字段：携带版本与候选，便于问题追溯
    modelVersion: str | None = None
    candidates: list[Candidate] = Field(default_factory=list)
    # 拒识标记：低置信时为真，表示模型无法确认具体犬种（可能是非犬宠物/模糊图）
    isUnknown: bool = False


class HealthPayload(BaseModel):
    status: str
    models: list[str] = Field(default_factory=list)
    provider: str = ""
    env: str = ""
