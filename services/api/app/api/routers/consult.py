"""问诊路由：AI 额度与分诊、医生问诊单、评价与报告全链路。

分诊是**规则引擎**（关键词 + 权重评分），不是大模型：结论、可能病因、建议科室
全部在服务端计算后一次性返回，前端只负责渲染。接入真实模型时只需替换
``_rule_triage`` / ``_structured_triage`` 两个函数的内部实现，契约不变。
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.ids import new_id
from app.models.consult_model import ConsultMessage, ConsultOrder, ConsultReport
from app.models.doctor import Doctor, DoctorReview
from app.models.extra import AiUsage, Setting
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.models.user import User

router = APIRouter(prefix="/consult", tags=["consult"])

# ── 平台设置（管理端「设置」页可改，读取时有默认值兜底） ──────────
_DEFAULT_AI_FREE = 3
_SETTINGS_KEY = "platform"


def _platform(db: DbSession) -> dict:
    row = db.get(Setting, _SETTINGS_KEY)
    return row.value if row and isinstance(row.value, dict) else {}


def _feature_enabled(db: DbSession, key: str) -> bool:
    return bool(_platform(db).get(key, True))


def _ai_daily_free(db: DbSession) -> int:
    try:
        return max(0, int(_platform(db).get("aiDailyFree", _DEFAULT_AI_FREE)))
    except (TypeError, ValueError):
        return _DEFAULT_AI_FREE


# ── 文本分诊规则 ────────────────────────────────────────────
TRIAGE_RULES = [
    {
        "level": "emergency",
        "keywords": ["呼吸困难", "张嘴呼吸", "抽搐", "癫痫", "大出血", "中毒", "巧克力", "误食",
                     "难产", "骨折", "昏迷", "中暑", "尿不出来", "尿闭", "肚子胀硬", "车祸", "高空坠落"],
        "label": "疑似急症", "short": "建议立即线下急诊",
        "advice": "这类情况线上问诊会延误治疗。请立即联系最近的 24 小时动物医院，途中保持宠物安静与体温。",
        "actions": ["立即前往最近的急诊医院", "途中不要强行喂水喂食", "如为误食，带上包装或残留物"],
    },
    {
        "level": "urgent",
        "keywords": ["呕吐", "拉血", "带血", "拒食", "不吃不喝", "发热", "发烧", "跛行",
                     "尿频", "尿血", "流脓", "肿大", "一直睡", "精神萎靡", "咳嗽"],
        "label": "建议尽快就诊", "short": "24 小时内预约医生",
        "advice": "症状需要专业检查才能确诊。建议 24 小时内完成一次面诊或线上问诊，不要自行用药。",
        "actions": ["记录症状开始时间与频次", "拍摄清晰照片或视频备用", "暂停自行给药，避免掩盖症状"],
    },
    {
        "level": "home",
        "keywords": ["掉毛", "梳毛", "皮屑", "轻微", "偶尔", "疫苗", "驱虫", "体重", "护理", "营养", "换粮"],
        "label": "可先居家观察", "short": "护理 + 观察 3 天",
        "advice": "目前未见明确危险信号。可按建议居家护理并观察 3 天，若加重或出现新症状再就诊。",
        "actions": ["按建议调整护理方式", "每日同一时间记录状态", "3 天未缓解则转为线上问诊"],
    },
]

# 关键词 → 可能病因（分诊卡的「可能原因」一栏）
_CAUSE_RULES = [
    (("耳朵", "挠耳"), ["耳螨", "真菌感染", "外耳道炎", "食物或环境过敏"]),
    (("呕吐",), ["进食过快或饮食不当", "毛球症", "胃肠炎", "异物梗阻"]),
    (("软便", "腹泻", "拉稀"), ["换粮应激", "肠道寄生虫", "菌群失调", "食物不耐受"]),
    (("皮肤", "红疹", "脱毛", "斑秃"), ["过敏性皮炎", "真菌感染", "跳蚤叮咬", "蠕形螨"]),
    (("食欲", "不吃", "挑食"), ["环境应激", "口腔或牙齿问题", "消化不适", "潜在发热性疾病"]),
    (("呼吸", "咳嗽", "喘"), ["上呼吸道感染", "过敏反应", "心脏问题", "气管异物"]),
    (("体重",), ["喂食过量", "运动量不足", "内分泌异常", "年龄相关代谢变化"]),
    (("掉毛", "皮屑"), ["季节性换毛", "营养不均衡", "皮肤疾病", "长期应激"]),
    (("眼", "泪"), ["结膜炎", "角膜损伤", "鼻泪管阻塞", "异物刺激"]),
    (("跛", "腿", "瘸"), ["软组织挫伤", "关节问题", "骨折", "趾间炎"]),
]
_CAUSE_FALLBACK = ["饮食与环境因素", "轻度感染", "应激反应", "品种相关易感问题"]

# 关键词 → 建议科室（与 /doctors 的科室 id 对齐）
_DEPT_RULES = [
    (("呼吸困难", "抽搐", "中毒", "误食", "骨折", "大出血"), "er"),
    (("皮肤", "耳朵", "掉毛", "红疹", "脱毛"), "derma"),
    (("跛", "腿", "伤口"), "surgery"),
    (("眼", "泪"), "eye"),
    (("体重", "胖", "喂"), "nutrition"),
    (("鸟", "兔", "龟"), "exotic"),
]
_DEPT_FALLBACK = "internal"


def _causes_of(text: str) -> list[str]:
    t = (text or "").lower()
    for keywords, causes in _CAUSE_RULES:
        if any(k in t for k in keywords):
            return causes
    return list(_CAUSE_FALLBACK)


def _dept_of(text: str) -> str:
    t = (text or "").lower()
    for keywords, dept in _DEPT_RULES:
        if any(k in t for k in keywords):
            return dept
    return _DEPT_FALLBACK


def _rule_triage(text: str) -> dict:
    t = (text or "").lower()
    for rule in TRIAGE_RULES:
        if any(kw in t for kw in rule["keywords"]):
            return {
                "level": rule["level"],
                "label": rule["label"],
                "short": rule["short"],
                "advice": rule["advice"],
                "causes": _causes_of(text),
                "actions": rule["actions"],
                "dept": "er" if rule["level"] == "emergency" else _dept_of(text),
                "confidence": "高" if rule["level"] == "emergency" else "中",
                "followUp": rule["advice"],
            }
    return {
        "level": "home", "label": "可先居家观察", "short": "护理 + 观察 3 天",
        "advice": "目前未见明确危险信号，可居家护理观察。",
        "causes": _causes_of(text), "actions": ["每日记录状态", "3 天未缓解则线上问诊"],
        "dept": _dept_of(text), "confidence": "中", "followUp": "观察 3 天",
    }

# ── 结构化预问诊评分（前端向导提交 ids，在这里加权） ────────────
_DURATION_W = {"today": 0, "2-3d": 1, "1w": 2, "1w+": 3}
_SEVERITY_W = {"mild": 0, "mid": 2, "severe": 4}
_SYMPTOM_W = {"blood-stool": 2, "breath-fast": 2, "vomit": 1, "diarrhea": 1, "appetite": 1}
_ACCOMPANY_W = {"spirit": 3, "appetite": 3, "fever": 2, "vomit-ac": 2,
                "diarrhea-ac": 2, "drink-ac": 1, "sleep": 1}
_PART_DEPT = {"head": "internal", "skin": "derma", "digest": "internal", "breath": "er",
              "limb": "surgery", "urinary": "internal", "behavior": "internal", "other": "general"}


def _structured_triage(p: dict) -> dict:
    score = 0
    factors = []
    symptom_labels = p.get("symptomLabels") or p.get("symptomIds") or []
    for sid in p.get("symptomIds") or []:
        w = _SYMPTOM_W.get(sid, 1)
        score += w
        factors.append({"text": f"症状：{sid}", "w": w})
    dur_w = _DURATION_W.get(p.get("durationId"), 0)
    score += dur_w
    if dur_w:
        factors.append({"text": f"已持续「{p.get('durationId')}」", "w": dur_w})
    sev_w = _SEVERITY_W.get(p.get("severityId"), 0)
    score += sev_w
    if sev_w:
        factors.append({"text": f"严重程度：{p.get('severityId')}", "w": sev_w})
    for aid in p.get("accompanyIds") or []:
        aw = _ACCOMPANY_W.get(aid, 1)
        score += aw
        factors.append({"text": f"伴随：{aid}", "w": aw})
    if score >= 3:
        level, label, short = "urgent", "建议尽快就诊", "24 小时内预约医生"
    else:
        level, label, short = "home", "可先居家观察", "护理 + 观察 3 天"
    return {
        "level": level, "score": score, "label": label, "short": short, "factors": factors,
        "dept": _PART_DEPT.get(p.get("partId"), "general"), "causes": symptom_labels,
        "advice": "建议 24 小时内完成一次线上或线下面诊。" if level == "urgent" else "可居家护理观察 3 天。",
        "actions": ["记录症状开始时间与频次", "拍摄清晰照片备用"],
        "confidence": "中", "followUp": "24h 内面诊" if level == "urgent" else "观察 3 天",
    }


# ── AI 额度 ────────────────────────────────────────────────
def _today() -> datetime.date:
    return datetime.date.today()


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _ai_quota(db: DbSession, uid: int) -> dict:
    rec = db.get(AiUsage, (uid, _today()))
    used = rec.used if rec else 0
    free = _ai_daily_free(db)
    return {"date": _today().isoformat(), "free": free, "used": used, "left": max(0, free - used)}


def _consume_ai_quota(db: DbSession, uid: int) -> dict:
    """扣减一次当日 AI 免费额度，并返回最新额度。"""
    today = _today()
    rec = db.get(AiUsage, (uid, today))
    if rec is None:
        rec = AiUsage(user_id=uid, stat_date=today, used=1)
        db.add(rec)
    else:
        rec.used = int(rec.used or 0) + 1
    db.commit()
    return _ai_quota(db, uid)


@router.get("/ai-quota", summary="AI 免费额度")
def ai_quota(user: CurrentUser, db: DbSession) -> dict:
    return ok(_ai_quota(db, _uid(user)))


@router.post("/triage", summary="AI 自由文本分诊（扣减当日免费额度）")
def triage(body: dict, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db, "consultEnabled"):
        raise AppError(ErrorCode.FORBIDDEN, "问诊功能维护中，暂不可用")
    uid = _uid(user)
    before = _ai_quota(db, uid)
    if before["left"] <= 0:
        raise AppError(ErrorCode.CONFLICT, "今日 AI 免费次数已用完")

    text = str(body.get("text", ""))
    result = _rule_triage(text)
    quota = _consume_ai_quota(db, uid)
    return ok(
        {
            "sessionId": new_id("cs_"),
            "triage": result,
            "reply": result["advice"],
            "quota": quota,
        }
    )


@router.post("/pre-consult", summary="结构化预问诊提交（返回分诊 + 落报告）")
def pre_consult(body: dict, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db, "consultEnabled"):
        raise AppError(ErrorCode.FORBIDDEN, "问诊功能维护中，暂不可用")
    result = _structured_triage(body)
    rid = new_id("rp")
    pet = db.get(Pet, body.get("petId"))
    report = ConsultReport(
        id=rid, user_id=_uid(user), type="ai",
        pet_id=body.get("petId"), pet_name=pet.name if pet else None,
        title=f"{pet.name if pet else '宠物'} · {str(body.get('note', ''))[:20]}",
        preview=result["label"], triage=result,
        # 前端若直接给出可读中文标签则优先使用，避免报告里只剩 id（如 skin-itch）
        chief={
            "partLabel": body.get("partLabel") or body.get("partId"),
            "symptomLabels": body.get("symptomLabels") or body.get("symptomIds") or [],
            "durationLabel": body.get("durationLabel") or body.get("durationId"),
            "severityLabel": body.get("severityLabel") or body.get("severityId"),
            "accompanyLabels": body.get("accompanyLabels") or body.get("accompanyIds") or [],
            "note": body.get("note"),
            "photos": body.get("photoCount", 0),
        },
        date=_today().isoformat(),
    )
    db.add(report)
    db.commit()
    return ok({"triage": result, "reportId": rid})


# ── 问诊单 ────────────────────────────────────────────────
def _order_out(o: ConsultOrder, db: DbSession) -> dict:
    doctor = db.get(Doctor, o.doctor_id) if str(o.doctor_id).isdigit() else None
    pet = db.get(Pet, o.pet_id)
    last = (
        db.query(ConsultMessage)
        .filter(ConsultMessage.order_id == o.id)
        .order_by(ConsultMessage.id.desc())
        .first()
    )
    return {
        "id": o.id, "doctorId": o.doctor_id, "mode": o.mode, "petId": o.pet_id,
        "state": o.state, "price": float(o.price or 0),
        "createdAt": o.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": o.summary,
        "doctor": {"id": doctor.id, "name": doctor.name, "deptLabel": doctor.dept_label} if doctor else None,
        "pet": {"id": pet.id, "name": pet.name} if pet else None,
        "lastMessage": {"type": last.type, "text": last.text} if last else None,
        "unread": 0,
    }


@router.get("/orders", summary="问诊单列表")
def list_orders(user: CurrentUser, db: DbSession, state: str | None = None) -> dict:
    q = db.query(ConsultOrder).filter(ConsultOrder.user_id == _uid(user))
    if state == "ongoing":
        q = q.filter(ConsultOrder.state.in_(["pending", "replied"]))
    rows = q.order_by(ConsultOrder.created_at.desc()).all()
    return ok([_order_out(o, db) for o in rows])


@router.post("/orders", summary="创建问诊单（下单）")
def create_order(body: dict, user: CurrentUser, db: DbSession) -> dict:
    if not _feature_enabled(db, "consultEnabled"):
        raise AppError(ErrorCode.FORBIDDEN, "问诊功能维护中，暂不可用")
    doctor = db.get(Doctor, body.get("doctorId"))
    pet = db.get(Pet, body.get("petId"))
    if doctor is None or pet is None or pet.owner_id != _uid(user):
        raise AppError(ErrorCode.BAD_REQUEST, "医生或宠物不存在")
    oid = new_id("o")
    price = body.get("price")
    if price is None:
        price = doctor.price or 0
    order = ConsultOrder(id=oid, user_id=_uid(user), doctor_id=doctor.id, pet_id=pet.id,
                         mode=body.get("mode", "text"), price=float(price),
                         state="pending", summary=body.get("summary"))
    db.add(order)
    db.add(ConsultMessage(order_id=oid, type="system", text=f"{doctor.name}医生已接诊，请描述宠物情况"))
    db.commit()
    return ok(_order_out(order, db))


@router.get("/orders/{order_id}", summary="问诊单详情（含消息）")
def order_detail(order_id: str, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    msgs = (
        db.query(ConsultMessage)
        .filter(ConsultMessage.order_id == order_id)
        .order_by(ConsultMessage.id.asc())
        .all()
    )
    out = _order_out(o, db)
    out["messages"] = [
        {"id": m.id, "type": m.type, "text": m.text, "images": m.images or [],
         "drugs": m.drugs or [], "note": m.note,
         "createdAt": m.created_at.strftime("%Y-%m-%dT%H:%M:%S")}
        for m in msgs
    ]
    return ok(out)


@router.post("/orders/{order_id}/messages", summary="发送消息")
def send_message(order_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    if o.state == "closed":
        raise AppError(ErrorCode.UNPROCESSABLE, "问诊已结束，无法发送消息")
    m = ConsultMessage(order_id=order_id, type="user", text=body.get("text"),
                       images=body.get("images", []))
    db.add(m)
    if o.state == "pending":
        o.state = "replied"
    db.commit()
    db.refresh(m)
    return ok({"id": m.id, "type": m.type, "text": m.text, "images": m.images or [],
               "createdAt": m.created_at.strftime("%Y-%m-%dT%H:%M:%S")})


@router.post("/orders/{order_id}/close", summary="结束问诊（自动生成真人报告）")
def close_order(order_id: str, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    o.state = "closed"
    o.closed_at = datetime.datetime.now()
    doctor = db.get(Doctor, o.doctor_id)
    rid = new_id("rp")
    pet = db.get(Pet, o.pet_id)
    report = ConsultReport(
        id=rid, user_id=_uid(user), type="human", pet_id=o.pet_id,
        pet_name=pet.name if pet else None,
        order_id=order_id, title=f"问诊报告 · {doctor.name if doctor else ''}",
        preview="真人问诊已完成",
        doctor={"id": doctor.id, "name": doctor.name, "title": doctor.title} if doctor else None,
        date=_today().isoformat(),
    )
    db.add(report)
    db.commit()
    return ok({**_order_out(o, db), "reportId": rid})


@router.post("/orders/{order_id}/rating", summary="提交评价（落库，医生评分取真实评价均值）")
def rate_order(order_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    if o.state != "closed":
        raise AppError(ErrorCode.UNPROCESSABLE, "问诊结束后才能评价")

    me = db.get(User, _uid(user))
    score = max(1, min(5, int(body.get("score", 5))))
    review = db.query(DoctorReview).filter(DoctorReview.order_id == order_id).first()
    if review is None:
        review = DoctorReview(
            doctor_id=str(o.doctor_id), user_id=_uid(user),
            user_name=(me.nickname if me else None) or "宠主", order_id=order_id,
        )
        db.add(review)
    review.score = score
    review.tags = body.get("tags") or []
    review.text = body.get("text")
    db.commit()

    # 评分与问诊数取真实评价聚合：有评价后 doctor.rating = 评价均值
    doctor = db.get(Doctor, o.doctor_id)
    if doctor is not None:
        reviews = (
            db.query(DoctorReview)
            .filter(DoctorReview.doctor_id == str(doctor.id))
            .all()
        )
        if reviews:
            doctor.rating = round(sum(r.score for r in reviews) / len(reviews), 1)
            doctor.consult_count = int(doctor.consult_count or 0) + 1
        db.commit()
    return ok({"orderId": order_id, "doctorId": o.doctor_id, "score": score,
               "tags": review.tags or []})


# ── 报告 ──────────────────────────────────────────────────
def _report_out(r: ConsultReport) -> dict:
    return {"id": r.id, "type": r.type, "petId": r.pet_id, "petName": r.pet_name, "title": r.title,
            "preview": r.preview, "date": r.date, "archived": bool(r.archived), "reminded": bool(r.reminded),
            "chief": r.chief, "triage": r.triage, "doctor": r.doctor,
            "doctorAdvice": r.doctor_advice, "rx": r.rx}


@router.get("/reports", summary="问诊报告列表")
def list_reports(
    user: CurrentUser,
    db: DbSession,
    type: str | None = None,
    pet_id: int | None = None,
) -> dict:
    q = db.query(ConsultReport).filter(ConsultReport.user_id == _uid(user))
    if type:
        q = q.filter(ConsultReport.type == type)
    if pet_id is not None:
        q = q.filter(ConsultReport.pet_id == pet_id)
    rows = q.order_by(ConsultReport.created_at.desc()).all()
    return ok({"list": [_report_out(r) for r in rows], "total": len(rows)})


@router.post("/reports", summary="保存问诊报告")
def save_report(body: dict, user: CurrentUser, db: DbSession) -> dict:
    rid = body.get("id") or new_id("rp")
    report = ConsultReport(
        id=rid, user_id=_uid(user), type=body.get("type", "ai"), pet_id=body.get("petId"),
        pet_name=body.get("petName"), order_id=body.get("orderId"), title=body.get("title"),
        preview=body.get("preview"), chief=body.get("chief"), triage=body.get("triage"),
        doctor=body.get("doctor"), doctor_advice=body.get("doctorAdvice"), rx=body.get("rx"),
        date=body.get("date") or _today().isoformat(),
    )
    db.add(report)
    db.commit()
    return ok(_report_out(report))


@router.get("/reports/{report_id}", summary="报告详情")
def report_detail(report_id: str, user: CurrentUser, db: DbSession) -> dict:
    r = db.get(ConsultReport, report_id)
    if r is None or r.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "报告不存在")
    return ok(_report_out(r))


@router.post("/reports/{report_id}/archive", summary="报告回流健康档案")
def archive_report(report_id: str, user: CurrentUser, db: DbSession) -> dict:
    r = db.get(ConsultReport, report_id)
    if r is None or r.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "报告不存在")
    if not r.archived:
        note = (f"【问诊报告】{(r.chief or {}).get('symptomLabels', [])} — "
                f"{(r.triage or {}).get('label', '')}。{(r.triage or {}).get('advice', '')}")
        db.add(HealthRecord(owner_id=_uid(user), pet_id=r.pet_id, kind="symptom",
                            record_date=_today(), note=note))
        r.archived = True
        db.commit()
    return ok({"archived": True, "recordId": r.id})


@router.post("/reports/{report_id}/remind", summary="报告转日程提醒")
def remind_report(report_id: str, user: CurrentUser, db: DbSession) -> dict:
    r = db.get(ConsultReport, report_id)
    if r is None or r.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "报告不存在")
    items = []
    if not r.reminded:
        rx = r.rx or {}
        if rx.get("drugs"):
            items.append({"title": f"按处方用药：{','.join(d.get('name', '') for d in rx['drugs'])}",
                          "date": (_today() + datetime.timedelta(days=1)).isoformat()})
        items.append({"title": "复诊：按医生建议回访",
                      "date": (_today() + datetime.timedelta(days=7)).isoformat()})
        for it in items:
            db.add(ScheduleItem(owner_id=_uid(user), pet_id=r.pet_id, title=it["title"],
                                category="other",
                                due_at=datetime.datetime.strptime(it["date"], "%Y-%m-%d"),
                                custom=True))
        r.reminded = True
        db.commit()
    return ok({"reminded": True, "items": items})
