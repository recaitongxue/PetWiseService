"""安全边界。

这一层是**不能跳过的**：它是"AI 不胡说"这件事的最后一道代码级保障。

三条硬规则：
1. 危险信号一票否决：命中即 emergency，无论其它得分多低；
2. 禁止处方：任何具体药物、剂量、给药频次的表述都要被拦截；
3. 免责声明必带：所有对外回答都必须带上，不可由模型决定是否省略。
"""

from __future__ import annotations

import re

from app.config import settings

# ── 危险信号词表 ─────────────────────────────────────────────
# 元组结构：(关键词, 描述, 权重)
RED_FLAGS: list[tuple[str, str, int]] = [
    ("呼吸困难", "呼吸困难/张口呼吸", 4),
    ("张口呼吸", "犬猫张口呼吸属急症", 4),
    ("抽搐", "抽搐或惊厥", 4),
    ("昏迷", "意识丧失", 4),
    ("休克", "休克表现", 4),
    ("大量出血", "活动性大出血", 4),
    ("无法排尿", "排尿障碍（尤其公猫尿闭）", 4),
    ("尿不出来", "排尿困难", 4),
    ("误食", "疑似误食异物/毒物", 3),
    ("呕吐不止", "持续性呕吐", 3),
    ("难产", "分娩困难", 4),
    ("中毒", "疑似中毒", 4),
    ("骨折", "疑似骨折", 3),
    ("眼球突出", "眼球突出/青光眼风险", 3),
    ("流产", "妊娠异常", 3),
    ("腹部膨大", "腹围突然增大（警惕胃扭转/腹水）", 3),
]

# ── 一般症状权重表 ───────────────────────────────────────────
SYMPTOM_WEIGHTS: list[tuple[str, str, int]] = [
    ("拒食", "完全不进食超过 24 小时", 2),
    ("不吃", "食欲下降", 1),
    ("精神", "精神沉郁", 2),
    ("呕吐", "呕吐", 2),
    ("腹泻", "腹泻", 1),
    ("便血", "便中带血", 3),
    ("血尿", "尿中带血", 3),
    ("咳嗽", "咳嗽", 1),
    ("打喷嚏", "打喷嚏", 1),
    ("流鼻涕", "鼻腔分泌物", 1),
    ("眼屎", "眼部分泌物增多", 1),
    ("流泪", "异常流泪", 1),
    ("瘙痒", "皮肤瘙痒", 1),
    ("脱毛", "局部脱毛", 1),
    ("跛行", "步态异常", 2),
    ("消瘦", "体重下降", 2),
    ("多饮", "饮水增多", 2),
    ("口臭", "口腔异味", 1),
]

_DURATION_WEIGHTS: dict[str, tuple[str, int]] = {
    "today": ("今天刚出现", 0),
    "1-2d": ("持续 1–2 天", 1),
    "2-3d": ("持续 2–3 天", 1),
    "1w": ("持续约一周", 2),
    "gt1w": ("持续超过一周", 3),
}

# 用户没选枚举时的中文兜底识别
_DURATION_TEXT_HINTS: list[tuple[str, str, int]] = [
    ("半个月", "持续半个月左右", 3),
    ("一个月", "持续一个月以上", 3),
    ("一周", "持续约一周", 2),
    ("两天", "持续 1–2 天", 1),
    ("今天", "今天刚出现", 0),
]

_SEVERITY_WEIGHTS: dict[str, tuple[str, int]] = {
    "mild": ("主人自评轻微", 0),
    "mid": ("主人自评一般", 1),
    "severe": ("主人自评严重", 3),
}

# ── 合规检查 ─────────────────────────────────────────────────
PRESCRIPTION_PATTERN = re.compile(
    r"\d+\s*(?:mg|毫升|ml|片|粒)|每日\s*\d+\s*次|一天\s*\d+\s*次|"
    r"阿莫西林|头孢|多西环素|恩诺沙星|甲硝唑|泼尼松|地塞米松|伊维菌素|"
    r"速诺|拜耳|大宠爱|福来恩",
    re.IGNORECASE,
)

_OVERCOMMIT_PATTERN = re.compile(r"肯定(?:没事|能好)|一定(?:没问题|有效)|保证|无需就医")


def detect_red_flags(text: str) -> list[dict[str, str | int]]:
    """返回命中的危险信号。"""
    hits = []
    for keyword, description, weight in RED_FLAGS:
        if keyword in text:
            hits.append({"text": description, "w": weight, "danger": True})
    return hits


def score_symptoms(text: str) -> list[dict[str, str | int]]:
    """返回一般症状的评分依据。"""
    factors = []
    for keyword, description, weight in SYMPTOM_WEIGHTS:
        if keyword in text:
            factors.append({"text": description, "w": weight, "danger": False})
    return factors


def score_duration(text: str, duration_key: str = "") -> dict[str, str | int] | None:
    if duration_key and duration_key in _DURATION_WEIGHTS:
        description, weight = _DURATION_WEIGHTS[duration_key]
        return {"text": description, "w": weight, "danger": False}

    for keyword, description, weight in _DURATION_TEXT_HINTS:
        if keyword in text:
            return {"text": description, "w": weight, "danger": False}
    return None


def score_severity(text: str, severity_key: str = "") -> dict[str, str | int] | None:
    if severity_key and severity_key in _SEVERITY_WEIGHTS:
        description, weight = _SEVERITY_WEIGHTS[severity_key]
        return {"text": description, "w": weight, "danger": False}
    for keyword, (description, weight) in _SEVERITY_WEIGHTS.items():
        if keyword in text:
            return {"text": description, "w": weight, "danger": False}
    return None


def level_of(score: int, has_danger: bool) -> str:
    """得分 → 等级。**危险信号一票否决**。"""
    if has_danger or score >= 7:
        return "emergency"
    if score >= 3:
        return "urgent"
    return "home"


def scan_prescription(text: str) -> list[str]:
    """找出处方级表述。"""
    return [m.group(0) for m in PRESCRIPTION_PATTERN.finditer(text or "")]


def scan_overcommit(text: str) -> list[str]:
    """找出过度承诺的表述。"""
    return [m.group(0) for m in _OVERCOMMIT_PATTERN.finditer(text or "")]


def compliance_check(text: str) -> dict[str, object]:
    """综合合规检查，返回给 critique 节点消费。"""
    hits_prescription = scan_prescription(text)
    hits_overcommit = scan_overcommit(text)

    issues: list[str] = []
    if hits_prescription and not settings.PRESCRIPTION_ENABLED:
        issues.append(f"含处方级表述：{'、'.join(hits_prescription[:3])}")
    if hits_overcommit:
        issues.append(f"过度承诺：{'、'.join(hits_overcommit[:3])}")

    return {
        "pass": not issues,
        "issues": issues,
        "needHuman": bool(hits_prescription),
    }


def with_disclaimer(text: str) -> str:
    """拼接免责声明。这是硬性要求，不留给模型决定。"""
    disclaimer = settings.DISCLAIMER
    if disclaimer in (text or ""):
        return text
    return f"{text}\n\n{disclaimer}"
