"""问诊路由：元信息字典、AI 额度与分诊、医生、问诊单与报告全链路。"""

from __future__ import annotations

import datetime
import json

from fastapi import APIRouter, Query, Response
from fastapi.responses import PlainTextResponse

from app.core.deps import CurrentUser, DbSession
from app.core.envelope import ok
from app.core.errors import AppError, ErrorCode
from app.core.serialize import public_doctor
from app.models.consult_model import ConsultMessage, ConsultOrder, ConsultReport
from app.models.doctor import Doctor
from app.models.extra import AiUsage
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.schemas.misc import DoctorOut

router = APIRouter(prefix="/consult", tags=["consult"])

# ── 静态字典（与前端向导一致） ──────────────────────────────
CONSULT_MODES = [
    {"id": "text", "label": "图文问诊", "icon": "comment", "price": 19, "desc": "上传照片与描述，医生 24h 内回复，可追问 3 次", "eta": "平均 8 分钟接诊"},
    {"id": "voice", "label": "电话问诊", "icon": "phone", "price": 39, "desc": "预约时段后医生直接致电，适合需要详细沟通", "eta": "15 分钟通话"},
    {"id": "video", "label": "视频问诊", "icon": "video", "price": 59, "desc": "面对面看诊，可实时展示患处与宠物状态", "eta": "20 分钟通话"},
]

CONSULT_DEPARTMENTS = [
    {"id": "all", "label": "全部", "icon": "stethoscope"},
    {"id": "internal", "label": "犬猫内科", "icon": "heart"},
    {"id": "surgery", "label": "外科骨科", "icon": "firstaid"},
    {"id": "derma", "label": "皮肤病", "icon": "sparkle"},
    {"id": "er", "label": "急诊重症", "icon": "alert"},
    {"id": "exotic", "label": "异宠专科", "icon": "paw"},
    {"id": "nutrition", "label": "营养体重", "icon": "scale"},
    {"id": "eye", "label": "眼科", "icon": "eye"},
]

DICTIONARY = {
    "bodyParts": [
        {"id": "head", "label": "头颈五官", "icon": "paw", "symptoms": [
            {"id": "ear-itch", "label": "频繁挠耳朵"}, {"id": "ear-discharge", "label": "耳道有分泌物或异味"},
            {"id": "eye-discharge", "label": "眼屎增多 / 眯眼"}, {"id": "sneeze", "label": "打喷嚏 / 流鼻涕"},
            {"id": "mouth", "label": "口臭 / 流涎 / 拒食硬物"}, {"id": "head-tilt", "label": "头部歪斜 / 转圈"}]},
        {"id": "skin", "label": "皮肤被毛", "icon": "sparkle", "symptoms": [
            {"id": "skin-itch", "label": "频繁挠抓或蹭蹭"}, {"id": "skin-loss", "label": "脱毛 / 斑秃"},
            {"id": "skin-rash", "label": "红疹 / 皮屑增多"}, {"id": "skin-lump", "label": "摸到肿块"}, {"id": "skin-lick", "label": "持续舔同一部位"}]},
        {"id": "digest", "label": "消化系统", "icon": "heart", "symptoms": [
            {"id": "vomit", "label": "呕吐"}, {"id": "diarrhea", "label": "软便 / 腹泻"},
            {"id": "appetite", "label": "食欲下降 / 拒食"}, {"id": "constipation", "label": "便秘 / 排便困难"},
            {"id": "blood-stool", "label": "便中带血", "redFlag": False, "weight": 2}]},
        {"id": "breath", "label": "呼吸循环", "icon": "heart", "symptoms": [
            {"id": "cough", "label": "咳嗽"}, {"id": "breath-fast", "label": "呼吸急促", "weight": 2},
            {"id": "breath-open", "label": "张嘴呼吸 / 喘不上气", "redFlag": True},
            {"id": "pale", "label": "舌色发白或发紫", "redFlag": True}, {"id": "faint", "label": "运动后虚脱 / 晕厥", "redFlag": True}]},
        {"id": "limb", "label": "四肢骨骼", "icon": "paw", "symptoms": [
            {"id": "lame", "label": "跛行 / 抬腿"}, {"id": "no-jump", "label": "不愿跳跃或上下楼"},
            {"id": "joint", "label": "关节肿胀 / 触碰疼痛"}, {"id": "paw", "label": "爪垫受伤 / 趾间红肿"},
            {"id": "paralysis", "label": "后肢无力 / 无法站立", "redFlag": True}]},
        {"id": "urinary", "label": "泌尿系统", "icon": "heart", "symptoms": [
            {"id": "urine-freq", "label": "尿频 / 到处乱尿"}, {"id": "urine-blood", "label": "尿中带血"},
            {"id": "urine-block", "label": "排尿困难 / 尿不出来", "redFlag": True}, {"id": "drink", "label": "饮水量明显变化"}]},
        {"id": "behavior", "label": "行为精神", "icon": "sparkle", "symptoms": [
            {"id": "spirit-low", "label": "精神萎靡 / 嗜睡"}, {"id": "hide", "label": "躲藏 / 不愿互动"},
            {"id": "aggression", "label": "性情改变 / 攻击性"}, {"id": "fit", "label": "抽搐 / 意识丧失", "redFlag": True}]},
        {"id": "other", "label": "其他", "icon": "notes", "symptoms": [
            {"id": "weight-loss", "label": "体重明显下降"}, {"id": "weight-gain", "label": "体重持续上升"},
            {"id": "poison", "label": "疑似误食异物或毒物", "redFlag": True}, {"id": "trauma", "label": "外伤 / 车祸 / 坠落", "redFlag": True},
            {"id": "postop", "label": "术后或产后护理"}]},
    ],
    "durations": [{"id": "today", "label": "今天刚开始", "w": 0}, {"id": "2-3d", "label": "2–3 天", "w": 1}, {"id": "1w", "label": "约一周", "w": 2}, {"id": "1w+", "label": "超过一周", "w": 3}],
    "severities": [{"id": "mild", "label": "轻微 · 吃喝玩正常", "w": 0}, {"id": "mid", "label": "明显不适 · 但能进食", "w": 2}, {"id": "severe", "label": "精神差 · 不吃不喝", "w": 4}],
    "accompanyOptions": [{"id": "spirit", "label": "精神萎靡", "w": 3}, {"id": "appetite", "label": "食欲下降", "w": 3}, {"id": "fever", "label": "身体发热 / 耳朵发烫", "w": 2}, {"id": "vomit-ac", "label": "呕吐", "w": 2}, {"id": "diarrhea-ac", "label": "腹泻", "w": 2}, {"id": "drink-ac", "label": "饮水异常", "w": 1}, {"id": "sleep", "label": "睡眠增多 / 躲藏", "w": 1}],
    "symptomGroups": [{"group": "消化", "items": ["呕吐", "软便腹泻", "食欲下降", "便秘"]}, {"group": "皮肤", "items": ["频繁挠抓", "脱毛斑秃", "皮肤红疹", "皮屑增多"]}, {"group": "头颈", "items": ["挠耳朵", "眼屎增多", "打喷嚏", "口臭流涎"]}, {"group": "全身", "items": ["精神萎靡", "跛行", "体重骤变", "呼吸异常"]}],
}

TRIAGE_RULES = [
    {"level": "emergency", "keywords": ["呼吸困难", "张嘴呼吸", "抽搐", "癫痫", "大出血", "中毒", "巧克力", "误食", "难产", "骨折", "昏迷", "中暑", "尿不出来", "尿闭", "肚子胀硬", "车祸", "高空坠落"], "label": "疑似急症", "short": "建议立即线下急诊", "advice": "这类情况线上问诊会延误治疗。请立即联系最近的 24 小时动物医院，途中保持宠物安静与体温。", "actions": ["立即前往最近的急诊医院", "途中不要强行喂水喂食", "如为误食，带上包装或残留物"]},
    {"level": "urgent", "keywords": ["呕吐", "拉血", "带血", "拒食", "不吃不喝", "发热", "发烧", "跛行", "尿频", "尿血", "流脓", "肿大", "一直睡", "精神萎靡", "咳嗽"], "label": "建议尽快就诊", "short": "24 小时内预约医生", "advice": "症状需要专业检查才能确诊。建议 24 小时内完成一次面诊或线上问诊，不要自行用药。", "actions": ["记录症状开始时间与频次", "拍摄清晰照片或视频备用", "暂停自行给药，避免掩盖症状"]},
    {"level": "home", "keywords": ["掉毛", "梳毛", "皮屑", "轻微", "偶尔", "疫苗", "驱虫", "体重", "护理", "营养", "换粮"], "label": "可先居家观察", "short": "护理 + 观察 3 天", "advice": "目前未见明确危险信号。可按建议居家护理并观察 3 天，若加重或出现新症状再就诊。", "actions": ["按建议调整护理方式", "每日同一时间记录状态", "3 天未缓解则转为线上问诊"]},
]

DURATION_W = {"today": 0, "2-3d": 1, "1w": 2, "1w+": 3}
SEVERITY_W = {"mild": 0, "mid": 2, "severe": 4}
PART_DEPT = {"head": "internal", "skin": "derma", "digest": "internal", "breath": "er", "limb": "surgery", "urinary": "internal", "behavior": "internal", "other": "general"}
SYMPTOM_W = {"blood-stool": 2, "breath-fast": 2, "vomit": 1, "diarrhea": 1, "appetite": 1}

AI_DAILY_FREE = 3


def _uid(user: CurrentUser) -> int:
    return int(user.user_id)


def _rule_triage(text: str) -> dict:
    t = (text or "").lower()
    for rule in TRIAGE_RULES:
        if any(kw in t for kw in rule["keywords"]):
            return {"level": rule["level"], "score": 10 if rule["level"] == "emergency" else 6,
                    "label": rule["label"], "short": rule["short"], "advice": rule["advice"],
                    "causes": [], "actions": rule["actions"], "factors": [], "dept": "er" if rule["level"] == "emergency" else "internal",
                    "followUp": rule["advice"]}
    return {"level": "home", "score": 0, "label": "可先居家观察", "short": "护理 + 观察 3 天",
            "advice": "目前未见明确危险信号，可居家护理观察。", "causes": [], "actions": ["每日记录状态", "3 天未缓解则线上问诊"], "factors": [], "dept": "general", "followUp": "观察 3 天"}


def _structured_triage(p: dict) -> dict:
    red_flag = False
    score = 0
    factors = []
    symptom_labels = p.get("symptomLabels", p.get("symptomIds", []))
    for sid in p.get("symptomIds", []):
        w = SYMPTOM_W.get(sid, 1)
        score += w
        factors.append({"text": f"症状：{sid}", "w": w})
    dur_w = DURATION_W.get(p.get("durationId"), 0)
    score += dur_w
    if dur_w:
        factors.append({"text": f"已持续「{p.get('durationId')}」", "w": dur_w})
    sev_w = SEVERITY_W.get(p.get("severityId"), 0)
    score += sev_w
    if sev_w:
        factors.append({"text": f"严重程度：{p.get('severityId')}", "w": sev_w})
    for aid in p.get("accompanyIds", []):
        aw = next((o["w"] for o in DICTIONARY["accompanyOptions"] if o["id"] == aid), 1)
        score += aw
        factors.append({"text": f"伴随：{aid}", "w": aw})
    if score >= 3 or red_flag:
        level, label, short = "urgent", "建议尽快就诊", "24 小时内预约医生"
    else:
        level, label, short = "home", "可先居家观察", "护理 + 观察 3 天"
    return {"level": level, "score": score, "label": label, "short": short, "factors": factors,
            "dept": PART_DEPT.get(p.get("partId"), "general"), "causes": symptom_labels,
            "advice": "建议 24 小时内完成一次线上或线下面诊。" if level == "urgent" else "可居家护理观察 3 天。",
            "actions": ["记录症状开始时间与频次", "拍摄清晰照片备用"], "followUp": "24h 内面诊" if level == "urgent" else "观察 3 天"}


def _today() -> datetime.date:
    return datetime.date.today()


def _ai_quota(db, uid) -> dict:
    rec = db.get(AiUsage, (uid, _today()))
    used = rec.used if rec else 0
    return {"date": _today().isoformat(), "free": AI_DAILY_FREE, "used": used, "left": max(0, AI_DAILY_FREE - used)}


@router.get("/modes", summary="问诊方式字典")
def consult_modes() -> dict:
    return ok(CONSULT_MODES)


@router.get("/departments", summary="问诊科室字典")
def consult_departments() -> dict:
    return ok(CONSULT_DEPARTMENTS)


@router.get("/dictionary", summary="结构化预问诊词典")
def dictionary() -> dict:
    return ok(DICTIONARY)


@router.get("/ai-quota", summary="AI 免费额度")
def ai_quota(user: CurrentUser, db: DbSession) -> dict:
    return ok(_ai_quota(db, _uid(user)))


@router.post("/triage", summary="AI 自由文本分诊")
def triage(body: dict, user: CurrentUser, db: DbSession) -> dict:
    text = body.get("text", "")
    triage = _rule_triage(text)
    return ok({"sessionId": f"cs_{int(datetime.datetime.now().timestamp())}", "triage": triage, "reply": triage["advice"], "quota": _ai_quota(db, _uid(user))})


@router.post("/pre-consult", summary="结构化预问诊提交（返回分诊 + 落报告）")
def pre_consult(body: dict, user: CurrentUser, db: DbSession) -> dict:
    triage = _structured_triage(body)
    rid = f"rp{int(datetime.datetime.now().timestamp())}"
    pet = db.get(Pet, body.get("petId"))
    report = ConsultReport(
        id=rid, user_id=_uid(user), type="ai",
        pet_id=body.get("petId"), pet_name=pet.name if pet else None,
        title=f"{pet.name if pet else '宠物'} · {body.get('note', '')[:20]}",
        preview=triage["label"], triage=triage,
        chief={"partLabel": body.get("partId"), "symptomLabels": body.get("symptomIds"), "durationLabel": body.get("durationId"), "severityLabel": body.get("severityId"), "accompanyLabels": body.get("accompanyIds"), "note": body.get("note"), "photos": body.get("photoCount", 0)},
        date=_today().isoformat(),
    )
    db.add(report)
    db.commit()
    return ok({"triage": triage, "reportId": rid})


@router.post("/case-summary", summary="AI 病例摘要（转真人时用）")
def case_summary(body: dict, user: CurrentUser, db: DbSession) -> dict:
    pet = db.get(Pet, body.get("petId"))
    summary = {
        "pet": {"id": pet.id, "name": pet.name, "breed": pet.breed, "age": pet.age if hasattr(pet, "age") else None, "weight": float(pet.weight or 0)} if pet else None,
        "symptoms": body.get("symptomLabels", []),
        "duration": body.get("durationLabel", ""),
        "severity": body.get("severityLabel", ""),
        "complaints": body.get("accompanyLabels", []),
        "aiTriage": body.get("triage", {}),
        "note": body.get("note", ""),
        "text": f"{pet.name if pet else '宠物'}：{body.get('note', '')}",
    }
    return ok({"summary": summary})


# ── 问诊单 ────────────────────────────────────────────────
def _order_out(o: ConsultOrder, db) -> dict:
    doctor = db.get(Doctor, o.doctor_id) if str(o.doctor_id).isdigit() else None
    pet = db.get(Pet, o.pet_id)
    last = db.query(ConsultMessage).filter(ConsultMessage.order_id == o.id).order_by(ConsultMessage.id.desc()).first()
    return {
        "id": o.id, "doctorId": o.doctor_id, "mode": o.mode, "petId": o.pet_id,
        "state": o.state, "price": float(o.price or 0), "createdAt": o.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": o.summary, "doctor": {"id": doctor.id, "name": doctor.name, "deptLabel": doctor.dept_label} if doctor else None,
        "pet": {"id": pet.id, "name": pet.name} if pet else None,
        "lastMessage": {"type": last.type, "text": last.text} if last else None, "unread": 0,
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
    doctor = db.get(Doctor, body.get("doctorId"))
    pet = db.get(Pet, body.get("petId"))
    if doctor is None or pet is None or pet.owner_id != _uid(user):
        raise AppError(ErrorCode.BAD_REQUEST, "医生或宠物不存在")
    oid = f"o{int(datetime.datetime.now().timestamp())}"
    order = ConsultOrder(id=oid, user_id=_uid(user), doctor_id=doctor.id, pet_id=pet.id,
                         mode=body.get("mode", "text"), price=float(body.get("price", doctor.price or 0)),
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
    msgs = db.query(ConsultMessage).filter(ConsultMessage.order_id == order_id).order_by(ConsultMessage.id.asc()).all()
    out = _order_out(o, db)
    out["messages"] = [{"id": m.id, "type": m.type, "text": m.text, "images": m.images or [], "drugs": m.drugs or [], "note": m.note, "createdAt": m.created_at.strftime("%Y-%m-%dT%H:%M:%S")} for m in msgs]
    return ok(out)


@router.get("/orders/{order_id}/messages", summary="拉取消息")
def order_messages(order_id: str, user: CurrentUser, db: DbSession, limit: int = 50) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    msgs = db.query(ConsultMessage).filter(ConsultMessage.order_id == order_id).order_by(ConsultMessage.id.desc()).limit(limit).all()
    return ok({"list": [{"id": m.id, "type": m.type, "text": m.text, "images": m.images or [], "drugs": m.drugs or [], "note": m.note, "createdAt": m.created_at.strftime("%Y-%m-%dT%H:%M:%S")} for m in reversed(msgs)], "hasMore": False})


@router.post("/orders/{order_id}/messages", summary="发送消息")
def send_message(order_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    if o.state == "closed":
        raise AppError(ErrorCode.UNPROCESSABLE, "问诊已结束，无法发送消息")
    m = ConsultMessage(order_id=order_id, type="user", text=body.get("text"), images=body.get("images", []))
    db.add(m)
    if o.state == "pending":
        o.state = "replied"
    db.commit()
    db.refresh(m)
    return ok({"id": m.id, "type": m.type, "text": m.text, "images": m.images or [], "createdAt": m.created_at.strftime("%Y-%m-%dT%H:%M:%S")})


@router.post("/orders/{order_id}/call", summary="发起通话（返回凭证）")
def call(order_id: str, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    return ok({"channel": f"pw_{order_id}", "token": f"rtc_{order_id}", "expiresIn": 3600})


@router.post("/orders/{order_id}/close", summary="结束问诊（自动生成真人报告）")
def close_order(order_id: str, user: CurrentUser, db: DbSession) -> dict:
    o = db.get(ConsultOrder, order_id)
    if o is None or o.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "问诊单不存在")
    o.state = "closed"
    o.closed_at = datetime.datetime.now()
    doctor = db.get(Doctor, o.doctor_id)
    rid = f"rp{int(datetime.datetime.now().timestamp())}"
    report = ConsultReport(id=rid, user_id=_uid(user), type="human", pet_id=o.pet_id,
                           pet_name=(db.get(Pet, o.pet_id).name if db.get(Pet, o.pet_id) else None),
                           order_id=order_id, title=f"问诊报告 · {doctor.name if doctor else ''}",
                           preview="真人问诊已完成", doctor={"id": doctor.id, "name": doctor.name, "title": doctor.title} if doctor else None,
                           date=_today().isoformat())
    db.add(report)
    db.commit()
    return ok({**_order_out(o, db), "reportId": rid})


@router.post("/orders/{order_id}/read", summary="标记消息已读")
def read_order(order_id: str, user: CurrentUser, db: DbSession) -> dict:
    return ok({"unread": 0})


@router.post("/orders/{order_id}/rating", summary="提交评价")
def rate_order(order_id: str, body: dict, user: CurrentUser, db: DbSession) -> dict:
    return ok({"orderId": order_id, "doctorId": body.get("doctorId"), "score": body.get("score"), "tags": body.get("tags", [])})


# ── 报告 ──────────────────────────────────────────────────
def _report_out(r: ConsultReport) -> dict:
    return {"id": r.id, "type": r.type, "petId": r.pet_id, "petName": r.pet_name, "title": r.title,
            "preview": r.preview, "date": r.date, "archived": bool(r.archived), "reminded": bool(r.reminded),
            "chief": r.chief, "triage": r.triage, "doctor": r.doctor, "doctorAdvice": r.doctor_advice, "rx": r.rx}


@router.get("/reports", summary="问诊报告列表")
def list_reports(user: CurrentUser, db: DbSession, type: str | None = None, pet_id: int | None = None) -> dict:
    q = db.query(ConsultReport).filter(ConsultReport.user_id == _uid(user))
    if type:
        q = q.filter(ConsultReport.type == type)
    if pet_id is not None:
        q = q.filter(ConsultReport.pet_id == pet_id)
    rows = q.order_by(ConsultReport.created_at.desc()).all()
    return ok({"list": [_report_out(r) for r in rows], "total": len(rows)})


@router.post("/reports", summary="保存问诊报告")
def save_report(body: dict, user: CurrentUser, db: DbSession) -> dict:
    rid = body.get("id") or f"rp{int(datetime.datetime.now().timestamp())}"
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
        note = f"【问诊报告】{(r.chief or {}).get('symptomLabels', [])} — {(r.triage or {}).get('label', '')}。{(r.triage or {}).get('advice', '')}"
        db.add(HealthRecord(owner_id=_uid(user), pet_id=r.pet_id, kind="symptom", record_date=_today(), note=note))
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
            items.append({"title": f"按处方用药：{','.join(d.get('name','') for d in rx['drugs'])}", "date": (_today() + datetime.timedelta(days=1)).isoformat()})
        items.append({"title": "复诊：按医生建议回访", "date": (_today() + datetime.timedelta(days=7)).isoformat()})
        for it in items:
            db.add(ScheduleItem(owner_id=_uid(user), pet_id=r.pet_id, title=it["title"], category="other", due_at=datetime.datetime.strptime(it["date"], "%Y-%m-%d"), custom=True))
        r.reminded = True
        db.commit()
    return ok({"reminded": True, "items": items})


@router.get("/reports/{report_id}/export", summary="导出报告（纯文本）")
def export_report(report_id: str, user: CurrentUser, db: DbSession) -> Response:
    r = db.get(ConsultReport, report_id)
    if r is None or r.user_id != _uid(user):
        raise AppError(ErrorCode.NOT_FOUND, "报告不存在")
    text = f"Petwise 问诊报告\n宠物：{r.pet_name}\n日期：{r.date}\n主诉：{json.dumps(r.chief or {}, ensure_ascii=False)}\n建议：{(r.triage or {}).get('advice','')}\n"
    return PlainTextResponse(text, media_type="text/plain; charset=utf-8")
