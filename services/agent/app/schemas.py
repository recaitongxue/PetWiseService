"""请求 / 响应结构。

TriageResult 字段与 contracts/openapi.yaml 完全对齐，
前端 TriageCard 直接消费，因此不允许重命名字段，只允许增加可选字段。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Factor(BaseModel):
    """可解释评分依据：回答时告诉用户"为什么给出这个结论"。"""

    text: str
    w: int | None = Field(default=None, description="该项权重")
    danger: bool = Field(default=False, description="是否危险信号")


class TriageResult(BaseModel):
    """分诊结论。"""

    level: Literal["emergency", "urgent", "home"]
    score: int
    label: str
    short: str
    advice: str
    causes: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    followUp: str = ""
    dept: str = Field(default="internal", description="推荐科室 id")
    factors: list[Factor] = Field(default_factory=list)
    # 非契约字段：知识来源与模型版本，供前端"追问依据"与问题追溯
    sources: list[str] = Field(default_factory=list)
    modelVersion: str = ""
    disclaimer: str = ""


class PetContext(BaseModel):
    """api 服务挑选后传来的结构化上下文。

    刻意不包含 Token、不包含未授权字段 —— 这一侧的可见范围就是这么大。
    """

    petId: str
    name: str = ""
    species: str = "all"
    breed: str = ""
    ageMonths: int | None = None
    weightKg: float | None = None
    neutered: bool | None = None
    vaccinated: bool | None = None
    chronic: list[str] = Field(default_factory=list)


class TriageRequest(BaseModel):
    """分诊请求。"""

    userId: str = ""
    complaint: str = Field(..., description="用户主诉原文")
    pet: PetContext | None = None
    duration: str = ""
    severity: str = ""
    symptoms: list[str] = Field(default_factory=list)
    photos: list[str] = Field(default_factory=list)
    stream: bool = False


class ReportRequest(BaseModel):
    """问诊报告生成请求。"""

    consultId: str
    userId: str = ""
    pet: PetContext | None = None
    transcript: list[dict[str, str]] = Field(default_factory=list)
    conclusion: str = ""


class SourceItem(BaseModel):
    """引用来源。"""

    title: str
    heading: str = ""
    score: float = 0.0
