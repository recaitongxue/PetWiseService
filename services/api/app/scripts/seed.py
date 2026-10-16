"""本地种子脚本：建表并灌入演示数据。

用法：
    uv run python -m app.scripts.seed            # 仅当库为空时灌入
    uv run python -m app.scripts.seed --reset     # 清空业务表后重新灌入

演示账号：手机号 13800138000（宠主）/ 13900000000（管理员），验证码登录（调试码 888888）。
"""

from __future__ import annotations

import datetime
import sys

from sqlalchemy import delete, func, select, text

from app.db import SessionLocal, create_all
from app.models.announcement import Announcement
from app.models.breed import Breed
from app.models.consult_model import ConsultMessage, ConsultOrder, ConsultReport
from app.models.doctor import Doctor, DoctorReview
from app.models.extra import AiUsage, AnnouncementDismiss, Memo, Recognition, Setting, WalletTx
from app.models.feedback import Feedback
from app.models.health import HealthRecord
from app.models.pet import Pet
from app.models.schedule import ScheduleItem
from app.models.social import (
    Comment,
    Contact,
    Conversation,
    Favorite,
    Message,
    Post,
    PostLike,
    PostReport,
)
from app.models.user import User

DEMO_PHONE = "13800138000"
ADMIN_PHONE = "13900000000"  # 管理端演示账号（role=admin）
NOW = datetime.datetime.now()
TODAY = datetime.date.today()


def _seed_breeds(db):
    rows = [
        Breed(
            species="cat", name="英国短毛猫", alias="英短",
            description="性格温顺、圆脸胖腮，适合家养。",
            traits={
                "sci": "Felis catus", "origin": "英国",
                "temperament": ["温顺", "安静", "黏人"],
                "care": "中等", "weight": "3.5~7.0kg", "life": "12-17年",
                "feeding": "定时定量，注意控制体重预防肥胖。",
                "issues": ["肥胖", "牙周病", "多囊肾"],
            },
            min_weight=3.5, max_weight=7.0, lifespan="12-17年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=british",
        ),
        Breed(
            species="cat", name="美国短毛猫", alias="美短",
            description="体质强健、亲人，适应力强。",
            traits={
                "sci": "Felis catus", "origin": "美国",
                "temperament": ["活泼", "亲人", "独立"],
                "care": "低", "weight": "3.5~7.0kg", "life": "13-16年",
                "feeding": "肠胃较好，常规优质猫粮即可。",
                "issues": ["肥厚型心肌病", "牙周病"],
            },
            min_weight=3.5, max_weight=7.0, lifespan="13-16年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=american",
        ),
        Breed(
            species="cat", name="布偶猫", alias="Ragdoll",
            description="体型大、被毛柔顺，黏人如布偶。",
            traits={
                "sci": "Felis catus", "origin": "美国",
                "temperament": ["黏人", "温和", "安静"],
                "care": "中高", "weight": "4.5~9.0kg", "life": "12-17年",
                "feeding": "长毛需化毛膏，注意饮水量。",
                "issues": ["遗传性肾病", "毛球症"],
            },
            min_weight=4.5, max_weight=9.0, lifespan="12-17年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=ragdoll",
        ),
        Breed(
            species="cat", name="中华田园猫", alias="橘猫/狸花猫",
            description="本土猫，好养皮实。",
            traits={
                "sci": "Felis catus", "origin": "中国",
                "temperament": ["独立", "机警", "亲人"],
                "care": "低", "weight": "3.0~6.0kg", "life": "13-18年",
                "feeding": "不挑食，注意定期驱虫。",
                "issues": ["寄生虫", "外伤"],
            },
            min_weight=3.0, max_weight=6.0, lifespan="13-18年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=tianyuan",
        ),
        Breed(
            species="dog", name="金毛寻回犬", alias="金毛",
            description="友善聪明，家庭伴侣犬首选。",
            traits={
                "sci": "Canis lupus familiaris", "origin": "英国",
                "temperament": ["友善", "聪明", "热情"],
                "care": "中高", "weight": "25.0~34.0kg", "life": "10-12年",
                "feeding": "大型犬粮，注意关节与体重管理。",
                "issues": ["髋关节发育不良", "皮肤过敏"],
            },
            min_weight=25.0, max_weight=34.0, lifespan="10-12年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=golden",
        ),
        Breed(
            species="dog", name="柯基犬", alias="Corgi",
            description="短腿萌系，精力旺盛需运动。",
            traits={
                "sci": "Canis lupus familiaris", "origin": "英国",
                "temperament": ["活泼", "警觉", "黏人"],
                "care": "中等", "weight": "10.0~14.0kg", "life": "12-15年",
                "feeding": "易胖，控制零食，补充软骨素。",
                "issues": ["椎间盘疾病", "肥胖"],
            },
            min_weight=10.0, max_weight=14.0, lifespan="12-15年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=corgi",
        ),
        Breed(
            species="dog", name="泰迪", alias="贵宾",
            description="不掉毛、体味小，城市常见。",
            traits={
                "sci": "Canis lupus familiaris", "origin": "法国",
                "temperament": ["机灵", "黏人", "活泼"],
                "care": "中高", "weight": "3.0~8.0kg", "life": "12-15年",
                "feeding": "小型犬粮，注意泪痕清洁。",
                "issues": ["髌骨脱位", "泪痕"],
            },
            min_weight=3.0, max_weight=8.0, lifespan="12-15年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=teddy",
        ),
        Breed(
            species="dog", name="中华田园犬", alias="土狗",
            description="本土犬，皮实好养。",
            traits={
                "sci": "Canis lupus familiaris", "origin": "中国",
                "temperament": ["忠诚", "机警", "独立"],
                "care": "低", "weight": "15.0~30.0kg", "life": "12-20年",
                "feeding": "不挑食，注意定期驱虫疫苗。",
                "issues": ["寄生虫", "外伤"],
            },
            min_weight=15.0, max_weight=30.0, lifespan="12-20年",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=tianyuan_dog",
        ),
    ]
    db.add_all(rows)
    db.commit()


def _seed_doctors(db):
    rows = [
        Doctor(
            name="陈静", title="主任医师", hospital="宠安动物医院",
            department="internal", dept_label="内科", years=15,
            specialties=["猫科", "消化内科", "肾脏"],
            good_at=["猫泌尿道综合征", "慢性肾衰", "呕吐腹泻"],
            rating=4.9, consult_count=1280, price=39.0, response_min=5,
            slot="今日 09:00-21:00", online=True,
            intro="从业 15 年，专注猫科与内科，擅长泌尿与肾脏疾病长期管理。",
            certs=["执业兽医师", "猫科医学会会员"],
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=chenjing",
        ),
        Doctor(
            name="李铭", title="主治医师", hospital="宠安动物医院",
            department="surgery", dept_label="外科", years=12,
            specialties=["软组织外科", "骨科"],
            good_at=["骨折内固定", "软组织肿瘤切除", "绝育"],
            rating=4.8, consult_count=860, price=49.0, response_min=8,
            slot="今日 13:00-20:00", online=True,
            intro="外科骨干，年手术量 300+，擅长骨折与软组织肿瘤。",
            certs=["执业兽医师", "小动物外科认证"],
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=liming",
        ),
        Doctor(
            name="王悦", title="副主任医师", hospital="喵汪联合诊所",
            department="derma", dept_label="皮肤科", years=9,
            specialties=["猫癣", "过敏"], good_at=["猫癣", "食物过敏", "外耳炎"],
            rating=4.7, consult_count=540, price=29.0, response_min=6,
            slot="今日 10:00-18:00", online=True,
            intro="皮肤与过敏方向，擅长顽固性猫癣与食物排查。",
            certs=["执业兽医师"],
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=wangyue",
        ),
        Doctor(
            name="张昊", title="主治医师", hospital="宠康医院",
            department="nutrition", dept_label="营养科", years=7,
            specialties=["肥胖管理", "幼宠喂养"], good_at=["减重管理", "幼宠喂养", "术后营养"],
            rating=4.6, consult_count=320, price=19.0, response_min=10,
            slot="明日 09:00-17:00", online=False,
            intro="营养与体重管理，帮上千只胖宠科学减重。",
            certs=["执业兽医师", "宠物营养师"],
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=zhanghao",
        ),
    ]
    db.add_all(rows)
    db.commit()


def _seed_announcements(db):
    rows = [
        Announcement(
            title="系统维护通知",
            content="本周日 02:00-04:00 进行服务升级，期间问诊可能短暂不可用。",
            level="warning", pinned=True, published_at=NOW,
        ),
        Announcement(
            title="秋季驱虫提醒",
            content="天气转凉，寄生虫仍活跃，建议为爱宠安排一次体内外驱虫。",
            level="info", pinned=False, published_at=NOW - datetime.timedelta(days=2),
        ),
        Announcement(
            title="新版健康档案上线",
            content="现已支持记录每日体重与状态评分，生成趋势曲线。",
            level="important", pinned=False, published_at=NOW - datetime.timedelta(days=5),
        ),
    ]
    db.add_all(rows)
    db.commit()


def _seed_user_and_pets(db):
    user = db.scalar(select(User).where(User.phone == DEMO_PHONE))
    if user is None:
        user = User(
            phone=DEMO_PHONE, nickname="林小满", balance=68.5, handle="@manman",
            bio="两只毛孩子的妈妈，记录每一天的可爱。",
            prefs={"personalized": True, "visibility": "public",
                   "binds": {"wechat": True, "apple": False}},
            blocked=[],
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    existing = db.scalar(select(func.count()).select_from(Pet).where(Pet.owner_id == user.id))
    if existing and existing > 0:
        return user

    mashu = Pet(
        owner_id=user.id, name="麻薯", species="cat", breed="中华田园猫",
        gender="female", birthday=datetime.date(2022, 6, 1), weight=4.2, neuter=True,
        tagline="软糯小太阳 ☀️", health_score=88,
        next_vaccine=TODAY + datetime.timedelta(days=30),
    )
    doudou = Pet(
        owner_id=user.id, name="豆豆", species="dog", breed="柯基犬",
        gender="male", birthday=datetime.date(2021, 3, 15), weight=11.5, neuter=True,
        tagline="短腿冲刺王 🏃", health_score=82,
        next_vaccine=TODAY + datetime.timedelta(days=20),
    )
    db.add_all([mashu, doudou])
    db.commit()
    db.refresh(mashu)
    db.refresh(doudou)

    # 健康记录（体重趋势）：两只宠物各 3 条
    db.add_all([
        HealthRecord(owner_id=user.id, pet_id=mashu.id, record_date=datetime.date(2024, 1, 1),
                     weight=3.9, metrics={"appetite": 5, "mood": 5, "stool": 5, "activity": 4}),
        HealthRecord(owner_id=user.id, pet_id=mashu.id, record_date=datetime.date(2024, 7, 1),
                     weight=4.0, metrics={"appetite": 4, "mood": 5, "stool": 4, "activity": 5}),
        HealthRecord(owner_id=user.id, pet_id=mashu.id, record_date=datetime.date(2025, 1, 1),
                     weight=4.2, metrics={"appetite": 5, "mood": 5, "stool": 5, "activity": 5}),
        HealthRecord(owner_id=user.id, pet_id=doudou.id, record_date=datetime.date(2024, 1, 1),
                     weight=10.8, metrics={"appetite": 5, "mood": 5, "stool": 5, "activity": 5}),
        HealthRecord(owner_id=user.id, pet_id=doudou.id, record_date=datetime.date(2024, 7, 1),
                     weight=11.2, metrics={"appetite": 5, "mood": 4, "stool": 5, "activity": 4}),
        HealthRecord(owner_id=user.id, pet_id=doudou.id, record_date=datetime.date(2025, 1, 1),
                     weight=11.5, metrics={"appetite": 5, "mood": 5, "stool": 5, "activity": 5}),
    ])
    db.commit()

    # 日程提醒：覆盖逾期 / 今天 / 未来，跨两只宠物（类别对齐 SCHEDULE_TYPES）
    db.add_all([
        ScheduleItem(owner_id=user.id, pet_id=mashu.id, title="体内驱虫", category="medication",
                     note="拜宠清 1/4 片", due_at=NOW - datetime.timedelta(days=3)),
        ScheduleItem(owner_id=user.id, pet_id=mashu.id, title="梳毛", category="groom",
                     due_at=NOW + datetime.timedelta(hours=3)),
        ScheduleItem(owner_id=user.id, pet_id=mashu.id, title="疫苗加强", category="vaccine",
                     due_at=NOW + datetime.timedelta(days=6)),
        ScheduleItem(owner_id=user.id, pet_id=doudou.id, title="遛弯", category="feed",
                     due_at=NOW + datetime.timedelta(hours=5)),
        ScheduleItem(owner_id=user.id, pet_id=doudou.id, title="体检", category="check",
                     due_at=NOW + datetime.timedelta(days=12)),
        ScheduleItem(owner_id=user.id, pet_id=mashu.id, title="狂犬疫苗", category="vaccine",
                     due_at=NOW - datetime.timedelta(days=40),
                     done=True, done_at=NOW - datetime.timedelta(days=40)),
    ])
    db.commit()
    return user


def _seed_social(db, user, pets, doctors):
    # 品种（收藏引用需要真实自增 ID）
    breeds = db.query(Breed).order_by(Breed.id.asc()).all()
    breed0 = breeds[0]
    # 通讯录
    friends = [
        Contact(
            id="ct1", owner_id=user.id, name="豆豆妈", kind="friend",
            bio="柯基同好 · 交流喂养", online=True, chat_id="c1",
            pet={"name": "年糕", "breed": "柯基犬", "age": 2},
            posts=12, fans="320",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=friend1",
        ),
        Contact(
            id="ct2", owner_id=user.id, name="橘座", kind="friend",
            bio="橘猫铲屎官", online=False,
            pet={"name": "大橘", "breed": "中华田园猫", "age": 4},
            posts=5, fans="88",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=friend2",
        ),
    ]
    vets = [
        Contact(
            id="ct3", owner_id=user.id, name="陈静 医生", kind="vet",
            bio="宠安动物医院 · 内科", online=True, doctor_id=str(doctors[0].id),
            posts=0, fans="",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=chenjing",
        ),
    ]
    groups = [
        Contact(
            id="ct4", owner_id=user.id, name="城市养猫交流群", kind="group",
            bio="1280 人 · 每日晒猫", online=True,
            posts=0, fans="",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=group1",
        ),
    ]
    db.add_all(friends + vets + groups)
    db.commit()

    # 会话（绑定到第一个好友）
    conv = Conversation(
        id="c1", owner_id=user.id, name="豆豆妈", kind="friend", online=True,
        last="周末一起遛狗呀～", time="09:12", unread=2,
        avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=friend1",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    db.add_all([
        Message(conversation_id=conv.id, owner_id=user.id, role="them",
                text="麻薯最近还吐吗？", time="09:10"),
        Message(conversation_id=conv.id, owner_id=user.id, role="me",
                text="好多了，换了处方粮～", time="09:11"),
        Message(conversation_id=conv.id, owner_id=user.id, role="them",
                text="周末一起遛狗呀～", time="09:12"),
    ])
    db.commit()

    # 帖子（社区）
    posts = [
        Post(
            id="p1", user_id=user.id, author="林小满", role="user",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=manman",
            text="麻薯今天第一次自己爬上了猫爬架顶层，老母亲甚感欣慰 🐾",
            images=[], tags=["日常", "英短"], likes=24, comments=3,
        ),
        Post(
            id="p2", user_id=None, author="宠安医院", role="vet",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=chenjing",
            text="【科普】换季掉毛期如何减少毛球症？每日梳毛 + 化毛膏，饮水机骗水有奇效。",
            images=[], tags=["科普", "护理"], likes=156, comments=12,
        ),
        Post(
            id="p3", user_id=None, author="橘座", role="user",
            avatar="https://api.dicebear.com/7.x/thumbs/svg?seed=friend2",
            text="大橘又胖了……有没有控制体重的靠谱粮推荐？",
            images=[], tags=["求助", "体重"], likes=9, comments=5,
        ),
    ]
    db.add_all(posts)
    db.commit()
    # 点赞（每用户一行；演示用户赞过 p1）
    db.add(PostLike(post_id="p1", user_id=user.id))
    db.commit()
    db.add_all([
        Comment(id="cm1", post_id="p1", user_id=user.id, name="橘座", text="太可爱了吧！"),
        Comment(id="cm2", post_id="p1", user_id=None, name="豆豆妈", text="麻薯好棒～"),
        Comment(id="cm3", post_id="p1", user_id=None, name="陈静 医生", text="多运动有助于消化哦"),
    ])
    db.commit()

    # 收藏
    db.add_all([
        Favorite(user_id=user.id, kind="breed", target_id=str(breed0.id), title=breed0.name,
                 desc="圆脸胖腮，温顺亲人", route=f"/breed/{breed0.id}"),
        Favorite(user_id=user.id, kind="post", target_id="p2", title="换季掉毛期护理科普",
                 desc="宠安医院", route="/post/p2"),
        Favorite(user_id=user.id, kind="tip", target_id="tip-feed", title="骗水小技巧",
                 desc="流动饮水机 + 湿粮拌水", route="/tip/feed"),
    ])
    db.commit()

    # 备忘录
    db.add_all([
        Memo(user_id=user.id, pet_id=pets[0].id, text="麻薯周五疫苗，记得空腹", pinned=True),
        Memo(user_id=user.id, pet_id=pets[1].id, text="豆豆驱虫药剩 1 次"),
    ])
    db.commit()
    return conv


def _seed_consult(db, user, pets, doctors):
    doctor = doctors[0]
    pet = pets[0]
    order = ConsultOrder(
        id="co1", user_id=user.id, doctor_id=str(doctor.id), pet_id=pet.id, mode="text",
        price=39.0, state="replied",
        summary={"chief": "软便 2 天，食欲下降", "petName": pet.name, "mode": "text"},
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    db.add_all([
        ConsultMessage(order_id=order.id, type="user",
                       text="麻薯这两天软便，不太爱吃饭，要紧吗？"),
        ConsultMessage(
            order_id=order.id, type="doctor",
            text="先观察精神与饮水量，建议禁食 12h 后少量喂易消化粮，若持续带血便请及时就诊。",
        ),
        ConsultMessage(order_id=order.id, type="user", text="好的，谢谢医生！"),
    ])
    db.commit()

    report = ConsultReport(
        id="rp1", user_id=user.id, type="human", pet_id=pet.id, pet_name=pet.name,
        order_id=order.id, title=f"{pet.name} 软便问诊报告",
        preview="精神尚可，考虑饮食应激型软便",
        chief={"text": "软便 2 天，食欲下降", "duration": "2天"},
        triage={"level": "low", "department": "internal", "redFlags": []},
        doctor={"id": str(doctor.id), "name": doctor.name,
                "title": doctor.title, "hospital": doctor.hospital},
        doctor_advice=(
            "禁食 12h 后少量易消化粮，补充益生菌；"
            "若 24h 内无改善或出现血便、精神沉郁，立即线下就诊。"
        ),
        rx={"drugs": [{"name": "宠物益生菌", "usage": "每日 1 包，拌食"},
                      {"name": "蒙脱石散", "usage": "便稀时半包"}]},
        archived=False, reminded=False, date=NOW.strftime("%Y-%m-%d"),
    )
    db.add(report)
    db.commit()

    # 一条识别历史（breed_id 用真实自增 ID）
    breed0 = db.query(Breed).order_by(Breed.id.asc()).first()
    db.add(Recognition(
        id="rc1", user_id=user.id, pet_id=pet.id, species="cat",
        predicted=breed0.name, sci=breed0.traits.get("sci", ""), confidence=0.92,
        breed_id=breed0.id,
        alternatives=[{"name": "美国短毛猫", "confidence": 0.7},
                      {"name": "布偶猫", "confidence": 0.55}],
        status="done",
    ))
    db.commit()

    # 今日 AI 额度（演示已用 1 次）
    db.add(AiUsage(user_id=user.id, stat_date=TODAY, used=1))
    db.commit()

    # 医生评价（真实评价表：医生评分取评价均值；doctor_id 用真实自增 ID）
    d1, d2, d3, d4 = doctors[0], doctors[1], doctors[2], doctors[3]
    db.add_all([
        DoctorReview(doctor_id=str(d1.id), user_id=user.id, user_name="林小满", order_id="co1",
                     score=5, tags=["专业", "有耐心"],
                     text="问得很细，最后只是小问题，省了一趟医院。"),
        DoctorReview(doctor_id=str(d1.id), user_id=None, user_name="豆豆妈", score=5,
                     text="有耐心，把用药剂量写得清清楚楚。"),
        DoctorReview(doctor_id=str(d2.id), user_id=None, user_name="年糕爸爸", score=5,
                     tags=["回复及时"], text="骨折咨询回复很快，方案讲得清楚。"),
        DoctorReview(doctor_id=str(d3.id), user_id=None, user_name="橘座本座", score=4,
                     text="猫癣排查很系统，就是回复稍微慢一点。"),
        DoctorReview(doctor_id=str(d4.id), user_id=None, user_name="胖橘控", score=5,
                     text="减重计划很专业，按月复盘。"),
    ])
    db.commit()

    # 医生评分 = 真实评价均值（与 rate_order 的维护逻辑一致）
    for d in doctors:
        scores = [r.score for r in db.query(DoctorReview).filter(
            DoctorReview.doctor_id == str(d.id)).all()]
        if scores:
            d.rating = round(sum(scores) / len(scores), 1)
    db.commit()

    # 钱包流水（与 User.balance=68.5 对账：充值 200 − 问诊 39 − 提现 92.5）
    db.add_all([
        WalletTx(user_id=user.id, type="topup", amount=200.0, note="余额充值",
                 created_at=NOW - datetime.timedelta(days=30)),
        WalletTx(user_id=user.id, type="withdraw", amount=39.0, note="问诊消费 · 陈静医生",
                 created_at=NOW - datetime.timedelta(days=9)),
        WalletTx(user_id=user.id, type="withdraw", amount=92.5, note="提现到微信",
                 created_at=NOW - datetime.timedelta(days=2)),
    ])
    db.commit()


def _seed_admin(db):
    """管理端演示账号：role=admin，用同一套验证码登录（调试码 888888）"""
    admin = db.query(User).filter(User.phone == ADMIN_PHONE).first()
    if admin is None:
        admin = User(phone=ADMIN_PHONE, nickname="平台管理员", role="admin", bio="Petwise 运营")
        db.add(admin)
    else:
        admin.role = "admin"
    db.commit()
    return admin


def _seed_feedbacks(db, user):
    if db.query(Feedback).count() > 0:
        return
    rows = [
        Feedback(user_id=user.id, type="suggestion",
                 content="希望识别结果页能直接一键加入日程提醒。",
                 contact="138****8000", status="pending"),
        Feedback(user_id=user.id, type="bug",
                 content="上传大图时偶尔会卡在识别中，刷新后才出结果。",
                 contact="wechat: manman", status="pending"),
        Feedback(user_id=user.id, type="complaint",
                 content="问诊医生回复太慢了，等了快一小时。",
                 contact=None, status="resolved"),
    ]
    db.add_all(rows)
    db.commit()


def _seed_reports(db, user):
    if db.query(PostReport).count() > 0:
        return
    posts = db.query(Post).order_by(Post.created_at.desc()).limit(2).all()
    rows = []
    for i, p in enumerate(posts):
        rows.append(
            PostReport(
                post_id=p.id,
                post_author=p.author,
                post_text=(p.text or "")[:200],
                user_id=user.id,
                reason="spam" if i == 0 else "inappropriate",
                note="疑似广告刷屏" if i == 0 else "图片内容不适合公开",
                status="pending",
            )
        )
    # 帖子不足时补一条占位举报，保证审核页有数据可演示
    if not rows:
        rows.append(
            PostReport(post_id="p1", post_author="阿橘的日常", post_text="演示举报内容",
                       user_id=user.id, reason="other", note="演示数据", status="pending")
        )
    db.add_all(rows)
    db.commit()


def _seed_settings(db):
    if db.get(Setting, "platform") is None:
        db.add(
            Setting(
                key="platform",
                value={"aiDailyFree": 3, "consultEnabled": True,
                       "communityEnabled": True, "recognizeEnabled": True},
            )
        )
        db.commit()


def _sync_schema(db):
    """create_all() 只建新表、不改旧表；--reset 时清理已知的陈旧列（幂等）。"""
    stale = {"posts": ["liked"]}  # liked 自 v1.0 起由 post_likes 每用户实时计算
    for table, cols in stale.items():
        existing = {
            row[0]
            for row in db.execute(
                text(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"
                ),
                {"t": table},
            )
        }
        for col in cols:
            if col in existing:
                db.execute(text(f"ALTER TABLE {table} DROP COLUMN {col}"))
                print(f"== schema: {table} 删除陈旧列 {col} ==")
    db.commit()


def reset(db):
    # 先删子表，避免外键约束
    db.execute(delete(PostReport))
    db.execute(delete(PostLike))
    db.execute(delete(DoctorReview))
    db.execute(delete(Comment))
    db.execute(delete(Post))
    db.execute(delete(ConsultMessage))
    db.execute(delete(ConsultReport))
    db.execute(delete(ConsultOrder))
    db.execute(delete(WalletTx))
    db.execute(delete(Message))
    db.execute(delete(Conversation))
    db.execute(delete(Contact))
    db.execute(delete(Favorite))
    db.execute(delete(Recognition))
    db.execute(delete(Memo))
    db.execute(delete(AnnouncementDismiss))
    db.execute(delete(AiUsage))
    db.execute(delete(Setting))
    db.execute(delete(ScheduleItem))
    db.execute(delete(HealthRecord))
    db.execute(delete(Pet))
    db.execute(delete(Feedback))
    db.execute(delete(Announcement))
    db.execute(delete(Doctor))
    db.execute(delete(Breed))
    db.execute(delete(User))
    db.commit()


def main():
    do_reset = "--reset" in sys.argv
    create_all()
    db = SessionLocal()
    try:
        if do_reset:
            print("== reset: 清空业务表 ==")
            _sync_schema(db)
            reset(db)
        seeded = db.scalar(select(func.count()).select_from(Breed)) or 0
        if seeded > 0 and not do_reset:
            print("已存在种子数据，跳过灌入（使用 --reset 可重置）。")
            return
        _seed_breeds(db)
        _seed_doctors(db)
        _seed_announcements(db)
        user = _seed_user_and_pets(db)
        pets = db.query(Pet).filter(Pet.owner_id == user.id).order_by(Pet.id.asc()).all()
        doctors = db.query(Doctor).order_by(Doctor.id.asc()).all()
        _seed_social(db, user, pets, doctors)
        _seed_consult(db, user, pets, doctors)
        _seed_feedbacks(db, user)
        _seed_reports(db, user)
        _seed_settings(db)
        admin = _seed_admin(db)
        print(
            f"种子完成：演示账号 {user.phone}（宠物 麻薯/豆豆），医生 {len(doctors)} 位；"
            f"管理端账号 {admin.phone}（role=admin）。"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
