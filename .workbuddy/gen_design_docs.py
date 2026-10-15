# -*- coding: utf-8 -*-
"""生成 docs/design/ 下的设计文档图片：每个页面一张功能流程图（SVG）+ 全局导航图 + HTML 总览。

用法：python .workbuddy/gen_design_docs.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "design"
FLOWS = OUT / "flows"

# ── 设计体系（与 app 端一致：暖纸白 + 深松绿墨 + 珊瑚强调） ─────────────────
C = {
    "bg": "#FBF8F2",
    "card": "#FFFFFF",
    "ink": "#1F2E26",
    "sub": "#5C6B62",
    "faint": "#8A968F",
    "line": "rgba(31,46,38,.14)",
    "pine": "#3E6B57",
    "pine_soft": "#EAF1EC",
    "coral": "#C96A4A",
    "coral_soft": "#F8ECE6",
    "sage": "#8FAE9B",
    "amber": "#C9973B",
    "amber_soft": "#F8F1DF",
    "grey_soft": "#EFEDE7",
}
STATUS = {
    "done": ("已实现", C["pine"], C["pine_soft"]),
    "demo": ("演示实现", C["amber"], C["amber_soft"]),
    "todo": ("占位", C["faint"], C["grey_soft"]),
}
W = 680  # 画布宽


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def text_w(s, size) -> float:
    """估算文本宽度：CJK 按 1.0em，ASCII 按 0.56em。"""
    return sum(size * (1.0 if ord(c) > 127 else 0.56) for c in str(s))


def chip(x, y, text, fill, color, w=None, size=11.5):
    """画一个胶囊 chip，返回 (svg, 结束x)。"""
    tw = text_w(text, size) + 18
    if w:
        tw = w
    return (
        f'<rect x="{x:.1f}" y="{y}" rx="{tw / 2:.1f}" height="22" width="{tw}" fill="{fill}"/>'
        f'<text x="{x + tw / 2:.1f}" y="{y + 15}" text-anchor="middle" font-size="{size}" fill="{color}">{esc(text)}</text>'
    ), x + tw + 8


def chip_row(x, y, items, fill, color, max_w=None):
    """一行 chips，超出换行。返回 (svg, 结束y)。"""
    parts, cx, cy = [], x, y
    for it in items:
        est = text_w(it, 11.5) + 18 + 8
        if max_w and cx + est > x + max_w:
            cx, cy = x, cy + 28
        s, cx = chip(cx, cy, it, fill, color)
        parts.append(s)
    return "".join(parts), cy + 22


def _tokens(text: str) -> list[str]:
    """切成排版单元：连续 ASCII 视为一个词，CJK 逐字，空格跟随前一单元。"""
    units, buf = [], ""
    for ch in str(text):
        if ord(ch) > 127:
            if buf:
                units.append(buf)
                buf = ""
            units.append(ch)
        elif ch == " ":
            buf += ch
            units.append(buf)
            buf = ""
        else:
            buf += ch
    if buf:
        units.append(buf)
    return units


def wrap(text, width_px: float, size: float, max_lines: int = 3) -> list[str]:
    """按实际字宽贪心断行（CJK 1.0em / ASCII 0.56em），英文单词不拆，超出截断加 …。"""
    lines, cur, curw = [], "", 0.0
    dropped = False
    for u in _tokens(text):
        w = sum(size * (1.0 if ord(c) > 127 else 0.56) for c in u)
        if cur and curw + w > width_px:
            lines.append(cur.rstrip())
            cur, curw = "", 0.0
            if len(lines) >= max_lines:
                dropped = True
                break
        cur += u
        curw += w
    if cur and len(lines) < max_lines:
        lines.append(cur.rstrip())
    elif cur:
        dropped = True
    if dropped and lines:
        lines[-1] = (lines[-1][:-1] + "…") if len(lines[-1]) > 1 else "…"
    return lines[:max_lines]


def step_card(x, y, w, h, title, desc):
    """步骤卡片：粗体标题 + 灰色小字说明（按字宽换行）。"""
    lines = wrap(desc, w - 20, 10.5)
    d = "".join(
        f'<text x="{x + 12}" y="{y + 40 + i * 13.5}" font-size="10.5" fill="{C["sub"]}">{esc(ln)}</text>'
        for i, ln in enumerate(lines)
    )
    return (
        f'<rect x="{x}" y="{y}" rx="10" width="{w}" height="{h}" fill="{C["card"]}" stroke="{C["line"]}"/>'
        f'<rect x="{x}" y="{y}" rx="10" width="4" height="{h}" fill="{C["pine"]}"/>'
        f'<text x="{x + 12}" y="{y + 22}" font-size="12.5" font-weight="600" fill="{C["ink"]}">{esc(title)}</text>'
        + d
    )


def arrow(x1, y1, x2, y2, color=None):
    color = color or C["sage"]
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.4"/>'
        f'<path d="M {x2} {y2} l -5 -2.4 l 5 -2.6 z" fill="{color}"/>'
    )


def page_svg(p: dict) -> str:
    """单页功能流程图。"""
    label, fg, bg = STATUS[p["status"]]
    steps = [{"t": s[0], "d": s[1] if len(s) > 1 else ""} for s in p["steps"]]
    # 布局：每行最多 4 张步骤卡
    per_row = 4
    rows = [steps[i : i + per_row] for i in range(0, len(steps), per_row)]
    card_w, card_h, gap = 148, 72, 22
    flow_h = len(rows) * card_h + (len(rows) - 1) * 14

    branches = p.get("branches", [])
    br_h = (len(branches) * 16 + 26) if branches else 0

    y = 64  # 入口行起点
    entry_svg, ey = chip_row(18, y, p["entry"], C["pine_soft"], C["pine"], max_w=W - 130)
    y = ey + 10

    flow_svg, flow_end = [], y
    for r, row in enumerate(rows):
        cx = 18
        for i, s in enumerate(row):
            flow_svg.append(step_card(cx, flow_end, card_w, card_h, s["t"], s.get("d", "")))
            if i < len(row) - 1:
                flow_svg.append(arrow(cx + card_w + 3, flow_end + card_h / 2, cx + card_w + gap - 4, flow_end + card_h / 2))
            cx += card_w + gap
        if r < len(rows) - 1:
            flow_svg.append(arrow(18 + card_w / 2, flow_end + card_h + 2, 18 + card_w / 2, flow_end + card_h + 12))
        flow_end += card_h + 14
    y = flow_end + 8

    br_svg = ""
    if branches:
        br_svg = (
            f'<rect x="18" y="{y}" rx="10" width="{W - 36}" height="{br_h - 8}" fill="{C["coral_soft"]}" '
            f'stroke="{C["coral"]}" stroke-dasharray="4 3" stroke-opacity=".45"/>'
            f'<text x="30" y="{y + 18}" font-size="11.5" font-weight="600" fill="{C["coral"]}">分支与规则</text>'
        )
        for i, b in enumerate(branches):
            br_svg += (
                f'<text x="30" y="{y + 36 + i * 16}" font-size="11" fill="{C["ink"]}">· {esc(b)}</text>'
            )
        y += br_h + 4

    data_svg, dy = chip_row(18, y + 4, p["data"], C["grey_soft"], C["ink"], max_w=W - 130)
    y = dy + 8
    exit_svg, ey2 = chip_row(18, y + 2, p["exits"], C["amber_soft"], "#8A6A1E", max_w=W - 130)
    y = ey2 + 12

    H = y
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="'PingFang SC','Microsoft YaHei',system-ui,sans-serif">
<rect width="{W}" height="{H}" rx="14" fill="{C['bg']}"/>
<rect x="18" y="16" rx="8" width="5" height="22" fill="{C['pine']}"/>
<text x="32" y="33" font-size="16.5" font-weight="700" fill="{C['ink']}">{esc(p['name'])}</text>
<text x="32" y="49" font-size="11" fill="{C['faint']}">{esc(p['route'])}</text>
<rect x="{W - 108}" y="18" rx="11" width="90" height="22" fill="{bg}"/>
<circle cx="{W - 94}" cy="29" r="3.4" fill="{fg}"/>
<text x="{W - 84}" y="33" font-size="11.5" font-weight="600" fill="{fg}">{esc(label)}</text>
<text x="18" y="{64 + 15}" font-size="11" font-weight="600" fill="{C['sub']}">入口</text>
{entry_svg}
<text x="18" y="{flow_start_y(rows, 64)}" font-size="11" font-weight="600" fill="{C['sub']}">流程</text>
{''.join(flow_svg)}
{br_svg}
<text x="18" y="{y - br_h - 8 if branches else y - 4}" font-size="11" font-weight="600" fill="{C['sub']}">数据源</text>
{data_svg}
<text x="18" y="{ey2 - 20}" font-size="11" font-weight="600" fill="{C['sub']}">出口</text>
{exit_svg}
</svg>"""


def flow_start_y(rows, y0):
    return y0 + 30 + 10 + 14  # 入口行之后


# ── 页面数据 ────────────────────────────────────────────────────────────────
PAGES: list[dict] = [
    # ═══ C 端 ═══
    dict(id="splash", group="C 端", name="启动页 Splash", route="/ （public）", status="demo",
         entry=["App 冷启动"],
         steps=[("读取登录态", "isAuthed() 同步读 localStorage"),
                ("按钮文案分流", "已登录「进入 Petwise」／未登录「开始使用」"),
                ("replace 跳转", "→ /home 或 /login，不留历史栈")],
         branches=["meta.public 放行，不被登录拦截", "隐藏 Dock（meta.bare）"],
         data=["petwise_auth", "→ authApi.me()"],
         exits=["/home", "/login"]),
    dict(id="login", group="C 端", name="登录 Login", route="/login （public）", status="demo",
         entry=["启动页", "守卫拦截", "退出登录"],
         steps=[("双 Tab 切换", "验证码 / 密码两种模式"),
                ("格式校验", "手机号 /^1[3-9]\\d{9}$/，验证码 6 位，密码 ≥6"),
                ("获取验证码", "60s 倒计时 + Toast 演示提示"),
                ("提交登录", "700ms 模拟 → login() 写 petwise_auth → 回跳")],
         branches=["未勾选协议 → Toast 拦截，不发请求", "微信登录 / 注册 / 忘记密码 → ⬜ Toast 占位", "加载态：按钮 spinner + disabled"],
         data=["ops.login()", "→ authApi.sendCode / login / me"],
         exits=["redirect 原路径", "/home"]),
    dict(id="home", group="C 端", name="首页 Home", route="/home", status="demo",
         entry=["Dock「今日」", "登录成功回跳"],
         steps=[("问候语分档", "按小时：夜深了/早安/午安/下午好/晚安"),
                ("平台公告", "折叠卡：active 且未被 dismissed"),
                ("宠物切换", "Tab + 头像，hero/趋势/提醒三处联动"),
                ("主角卡", "健康分环 ≥85 绿 / ≥70 黄 / <70 红"),
                ("今日提醒", "「知道了」⚠ 只 Toast 不落盘"),
                ("快捷磁贴", "AI 问诊（3 次/日）/ 识别 / 社区 / 档案"),
                ("本周趋势", "7 天均值 + 柱状图（优→珊瑚）")],
         branches=["公告区无数据整块不渲染", "全页无加载态、无错误态"],
         data=["mock.pets → GET /pets", "petTrends → health-trend", "petReminders → reminders", "announcements → GET /announcements"],
         exits=["/recognize", "/consult/ai", "/community", "/pet/:id", "/schedule"]),
    dict(id="recognize", group="C 端", name="拍照识别 Recognize", route="/recognize", status="demo",
         entry=["首页磁贴", "我的→＋添加宠物"],
         steps=[("触发识别", "快门 runScan() 1600ms / 相册选图 / 示例库"),
                ("取景框四态", "真实照片→放入框内→识别中扫描线→结果"),
                ("结果卡", "品种 + 置信度 + 4 项指标（good/watch）"),
                ("后续操作", "重新识别 / 保存记录 / 百科 / 问医生")],
         branches=["相册：真实 input file + createObjectURL 预览", "示例库卡片立即出结果无延迟", "⚠ 指标为 mock 写死，页面无分级算法", "⚠ history 存内存，刷新丢失"],
         data=["mock.recognitionSamples", "→ POST /recognitions（multipart 调 vision）"],
         exits=["/breed/:id", "/consult/ai?pet=&note="]),
    dict(id="breed", group="C 端", name="品种百科 BreedDetail", route="/breed/:id", status="demo",
         entry=["识别结果「品种百科」", "收藏", "社区帖子"],
         steps=[("查表解析", "id 精确 → name 匹配 → 未命中提示"),
                ("档案 hero", "插图 + 中文名 + 拉丁名 + 科属 + 原产地"),
                ("体重 / 寿命", "双栏数据"),
                ("三大区块", "01 性格特质 chips / 02 易患问题 / 03 护理要点"),
                ("底部 CTA", "「就这个品种问一问」带上下文跳转")],
         branches=["演示库 6 品种：英短/柯基/布偶/金毛/田园猫/暹罗"],
         data=["mock.breedLibrary", "→ GET /breeds、GET /breeds/{id}"],
         exits=["/consult/ai?pet=&note="]),
    dict(id="pet", group="C 端", name="宠物档案 PetProfile", route="/pet/:id", status="done",
         entry=["首页「健康档案」chip", "我的→宠物卡片"],
         steps=[("档案 hero", "基础信息 + 健康分"),
                ("＋ 记录体重", "预填当前体重，step 0.1"),
                ("类型 chip 4 种", "体重/饮食/症状/护理，仅体重有数字框"),
                ("保存校验", "date 必有 + 体重有值或有备注"),
                ("趋势合成", "归月取最新 → 覆盖/追加 → 排序 → 柱高归一"),
                ("记录时间轴", "用户录入置顶 + 3 条内置")],
         branches=["症状类自动标黄（watch）", "diff>0.05 略增 / <-0.05 略减 / 否则稳定", "宠物不存在 → 「未找到该宠物档案」"],
         data=["petwise_pet_records（与报告归档共用同一键）", "→ GET/POST /pets/{id}/weights、records"],
         exits=["/consult/ai", "/schedule"]),
    dict(id="schedule", group="C 端", name="日程与提醒 Schedule", route="/schedule", status="demo",
         entry=["我的→提醒与日程", "首页今日提醒"],
         steps=[("筛选 chip", "全部 + 每只宠物"),
                ("＋ 新建", "归属宠物继承当前筛选"),
                ("6 类类型", "疫苗/驱虫/体检/称重/洗护/自定义"),
                ("完成 / 撤销", "✓ Toast「已完成」/ 撤销回待办")],
         branches=["逾期：diff<0 加红标，不单独分组", "dateText：今天/明天/后天/N 天前/N 天后", "⚠「全部」筛选时空态文案仍称「这只宠物」"],
         data=["petwise_schedule_done", "petwise_schedule_custom", "→ GET /schedule、POST、PATCH done"],
         exits=["—"]),
    dict(id="hub", group="C 端", name="问诊中枢 ConsultHub", route="/consult", status="demo",
         entry=["Dock 中央凸起 FAB"],
         steps=[("三大入口", "AI 智能问诊 / 结构化预问诊 / 真人医生"),
                ("问诊记录", "带计数入口")],
         branches=[],
         data=["mock", "→ 各问诊接口"],
         exits=["/consult/ai", "/preconsult", "/doctors", "/records"]),
    dict(id="consult", group="C 端", name="AI 智能问诊 Consult", route="/consult/ai", status="demo",
         entry=["首页磁贴", "识别结果问医生", "档案问诊", "百科 CTA"],
         steps=[("带上下文进入", "query.pet/note → AI 首条问候"),
                ("守卫 1", "输入为空或 typing 中 → return"),
                ("守卫 2", "额度 ≤0 → Toast + 跳医生列表"),
                ("发送", "push me → 1300ms → 分诊卡/文本+3 chip"),
                ("回复后扣额度", "consumeAiQuota() 在回复生成之后")],
         branches=["⚠ 非真流式：typing 占位 + 一次性插入", "上下文横幅可 × 清除", "emergency → 急诊告警条 + 急诊按钮", "额度条常驻「剩余 n/3」", "转真人写 sessionStorage 病例摘要"],
         data=["ops AI 配额 3 次/日", "→ agent SSE /internal/v1/triage/stream"],
         exits=["/doctors（goDoctors）"]),
    dict(id="preconsult", group="C 端", name="结构化预问诊 PreConsult", route="/preconsult", status="done",
         entry=["问诊中枢"],
         steps=[("7 步问卷", "宠物→部位8→症状多选→时长→精神进食→伴随→补充"),
                ("逐步校验", "必选/至少1项/切换部位清空症状"),
                ("评分引擎", "redFlag 8 条一票否决 → emergency,10"),
                ("加权累加", "时长0-3 + 严重度0-4 + 加重项 + 伴随"),
                ("分级产出", "score≥3 urgent，否则 home"),
                ("生成报告", "factor 可解释 → saveReport → replace")],
         branches=["高危即时告警 + 急诊直达，但不打断问卷", "⚠ 无草稿机制，中途退出全丢失", "照片上传 ⬜ 数量模拟"],
         data=["data/triage.js（与后端约定一致）", "→ POST /consult/triage"],
         exits=["/report/<id>"]),
    dict(id="doctors", group="C 端", name="医生列表 Doctors", route="/doctors", status="demo",
         entry=["AI 问诊升级", "预问诊高危", "报告页转真人", "问诊中枢"],
         steps=[("科室 chip", "8 科室，query.dept 统一推导"),
                ("排序", "在线优先 → 评分降 → 响应升"),
                ("医生卡片", "评分/接诊量/¥19 起/响应时间"),
                ("AI 病例摘要卡", "读 sessionStorage，可展开")],
         branches=["空态：「该科室暂无在线医生…」"],
         data=["sessionStorage petwise_case_summary", "mock.doctors → GET /doctors?dept="],
         exits=["/doctor/:id"]),
    dict(id="doctor", group="C 端", name="医生详情 DoctorDetail", route="/doctor/:id", status="demo",
         entry=["医生列表卡片"],
         steps=[("医生 hero", "评分/接诊量/执业年三宫格"),
                ("排班与擅长", "排班条 + 擅长领域 + 资质"),
                ("病例摘要区", "有摘要可补充，无摘要手填"),
                ("方式三选一", "图文 ¥19 / 电话 ¥39 / 视频 ¥59"),
                ("提交下单", "createConsultOrder → replace 问诊室")],
         branches=["底部提示：接诊前可取消全额退款"],
         data=["mock", "→ POST /consult/orders"],
         exits=["/consultation/<orderId>"]),
    dict(id="room", group="C 端", name="问诊室 ConsultationRoom", route="/consultation/:id", status="demo",
         entry=["医生详情下单", "问诊记录点击"],
         steps=[("进入", "系统条「已提交，N 分钟内接诊」"),
                ("医生首轮", "1500ms 后「已看过 AI 初步判断…」"),
                ("对话脚本", "用户发 → 1200ms typing → 下一条"),
                ("处方卡", "第 2 轮后 900ms 推送 rx 卡片"),
                ("状态流转", "pending → replied")],
         branches=["通话卡：视频→发起视频 / 电话→呼叫 ⬜ 仅 Toast", "⚠ state=replied 只改内存，刷新回 pending", "消息类型：system/text/rx"],
         data=["petwise_consult_orders（消息持久化）", "→ WS / SSE"],
         exits=["评价弹层 → 报告页"]),
    dict(id="report", group="C 端", name="问诊报告 Report", route="/report/:id", status="demo",
         entry=["预问诊产出", "问诊室评价后生成"],
         steps=[("封面", "类型徽标 ai/human"),
                ("主诉分区", "表现/持续/状态/伴随/补充/附件"),
                ("分诊结论", "TriageCard，置信度 emergency→高"),
                ("评分依据", "factor 逐条 +w，danger 标红"),
                ("医生建议/用药/复查", "human 报告含 rx 结构化处方")],
         branches=["存入档案 → petwise_pet_records（幂等）", "用药提醒 → 次日用药 + 复查日程（home +3 天 / 其它 +7 天）", "导出 ⬜ 仅 Toast 提示截图"],
         data=["reports（ops）", "→ GET /consult/reports/{id}"],
         exits=["/doctors?dept=", "健康档案", "日程"]),
    dict(id="records", group="C 端", name="问诊记录 Records", route="/records", status="demo",
         entry=["我的→问诊记录", "Dock 问诊域"],
         steps=[("Tab 切换", "全部 / 智能问诊 / 真人医生（带计数）"),
                ("三源聚合", "[...报告, ...订单, ...内置] 固定顺序"),
                ("卡片渲染", "类型/标题/日期/摘要/宠物/医生/状态"),
                ("点击跳转", "reportId 优先 → 报告页，orderId → 问诊室")],
         branches=["⚠ AI 内置记录两者皆空 → 点击无反应", "状态：AI 已完成 / pending 待接诊 / replied 已回复"],
         data=["ops", "→ GET /consult/records"],
         exits=["/report/:id", "/consultation/:id", "/consult/ai", "/doctors"]),
    dict(id="community", group="C 端", name="宠物社区 Community", route="/community", status="demo",
         entry=["Dock 社区", "首页 Banner"],
         steps=[("Tab 推荐/关注", "关注流 = 奇数下标（模拟关系）"),
                ("话题 chip", "6 话题，再点取消"),
                ("点赞 / 评论", "本地 ±1 + 动画 / 面板打开重置 mock"),
                ("发布", "≤3 图，发布后回推荐 + 清筛选")],
         branches=["⚠ 内容不持久化，刷新丢失", "⬜ 关注/分享按钮纯装饰", "图片为色块占位，非真实上传"],
         data=["mock.posts", "→ GET /posts"],
         exits=["/breed/:id", "/pet/:id"]),
    dict(id="chatlist", group="C 端", name="消息列表 ChatList", route="/chat", status="demo",
         entry=["Dock 消息"],
         steps=[("会话列表", "头像/在线点/最后一条/时间"),
                ("未读徽标", "mock 合计 2，Dock 同步"),
                ("类型 pill", "兽医 / 群聊 / 好友")],
         branches=["⬜ 未读不清零、无搜索"],
         data=["mock.chats", "→ imApi.conversations"],
         exits=["/chat/:id"]),
    dict(id="chatroom", group="C 端", name="聊天室 ChatRoom", route="/chat/:id", status="demo",
         entry=["消息列表会话"],
         steps=[("气泡消息", "HH:mm 时间戳"),
                ("发送", "1100ms 对方「正在输入」"),
                ("自动回复", "固定文案「收到～ 我看看」")],
         branches=["⬜ 表情/分享/WebSocket 未实现"],
         data=["mock.messages", "→ WS /messages"],
         exits=["—"]),
    dict(id="favorites", group="C 端", name="我的收藏 Favorites", route="/favorites", status="demo",
         entry=["我的→我的收藏"],
         steps=[("4 类筛选", "全部 / 品种 / 帖子 / 贴士"),
                ("整行跳转", "按类型去详情页"),
                ("取消收藏", "右侧 ×")],
         branches=["⚠ 取消只存内存，刷新后收藏复活"],
         data=["mock.favorites", "→ GET /favorites"],
         exits=["/breed/:id", "/community"]),
    dict(id="profile", group="C 端", name="我的 Profile", route="/profile", status="demo",
         entry=["Dock 我的"],
         steps=[("用户卡", "脱敏手机 138****8888"),
                ("我的宠物", "→ 档案；＋添加实际跳识别页"),
                ("功能菜单", "记录(5)/收藏(4)/日程/反馈/关于"),
                ("意见反馈", "3 类 → 写 petwise_feedbacks"),
                ("退出登录", "清 auth → replace /login")],
         branches=["✅ 反馈真实双端闭环（管理端可见）", "⬜ 编辑资料为 Toast 占位"],
         data=["petwise_feedbacks", "→ adminApi.feedbacks"],
         exits=["/records", "/favorites", "/schedule", "/recognize", "/pet/:id", "/login"]),
    # ═══ 管理端 ═══
    dict(id="admin-login", group="管理端", name="管理端登录 Login", route="/login", status="demo",
         entry=["未登录访问", "退出登录"],
         steps=[("账号密码", "admin / petwise 字符串比对"),
                ("写登录标记", "petwise_admin_auth = '1'"),
                ("守卫分流", "已登录访问登录页 → 跳看板")],
         branches=["⚠ 无 token、无过期、无角色"],
         data=["localStorage 单标记"],
         exits=["/dashboard"]),
    dict(id="admin-dashboard", group="管理端", name="数据看板 Dashboard", route="/dashboard", status="demo",
         entry=["登录成功", "侧栏菜单"],
         steps=[("4 张指标卡", "用户 12,846 / 宠物 17,230 / 识别 1,342 / 问诊 386"),
                ("双折线图", "手写 SVG：识别·珊瑚 / 问诊·松绿"),
                ("品种分布", "进度条（⚠ 分母硬编码 30）"),
                ("运营速览", "3 条（⚠ 数字硬编码）")],
         branches=["⬜ 无时间范围切换 / 刷新 / 导出", "环境标签「CV + LLM 服务正常」为硬编码文案"],
         data=["data/admin.js 静态数组", "零 HTTP 调用"],
         exits=["各管理页"]),
    dict(id="admin-users", group="管理端", name="用户管理 Users", route="/users", status="demo",
         entry=["侧栏菜单"],
         steps=[("搜索 / 筛选", "姓名或手机号；全部/正常/已冻结"),
                ("列表渲染", "用户/手机/宠物数/注册时间/状态"),
                ("抽屉详情", "账号状态卡 + 名下宠物 + 治理操作"),
                ("冻结 / 恢复", "改内存状态")],
         branches=["⚠ 冻结只改内存，刷新失效", "⚠ 宠物数按 pets.filter(owner===name) 计算", "⬜ 重置密码/导出仅 Toast"],
         data=["data/admin.js"],
         exits=["—"]),
    dict(id="admin-records", group="管理端", name="识别记录 Records", route="/records", status="demo",
         entry=["侧栏菜单"],
         steps=[("列表渲染", "编号/用户/宠物/结果/置信度/时间/状态"),
                ("置信度分级", "≥0.85 good / ≥0.60 mid / <0.60 low")],
         branches=["⬜ 无排序/分页/详情/复核动作", "⚠ 不读 Settings 里的置信度阈值"],
         data=["data/admin.js 静态"],
         exits=["—"]),
    dict(id="admin-moderation", group="管理端", name="内容审核 Moderation", route="/moderation", status="demo",
         entry=["侧栏菜单（徽标硬编码 2）"],
         steps=[("筛选", "全部 / 待审核 / 已通过"),
                ("待审卡片", "文本标红"),
                ("通过 / 驳回", "pass / reject + Toast")],
         branches=["⬜ 无驳回理由/申诉/图片预览/批量", "⚠「敏感词初筛命中 1 条」硬编码，与词库无联动"],
         data=["data/admin.js"],
         exits=["—"]),
    dict(id="admin-consults", group="管理端", name="问诊记录 Consults", route="/consults", status="demo",
         entry=["侧栏菜单"],
         steps=[("表格渲染", "编号/用户/宠物/主题/轮次/模型/时间/状态"),
                ("模型标签", "GLM-4V（图文）/ GLM-4（纯文本）")],
         branches=["⬜ 无会话回放 / 转人工跟进 / 导出"],
         data=["data/admin.js 静态"],
         exits=["—"]),
    dict(id="admin-announce", group="管理端", name="公告管理 Announce", route="/announce", status="done",
         entry=["侧栏菜单"],
         steps=[("表单填写", "标题必填 / 类型 select / 正文必填"),
                ("发布", "unshift + 持久化 + Toast「首页将同步展示」"),
                ("行操作", "上线/下线（active 取反）/ 删除")],
         branches=["✅ 真实双端闭环：App 首页读同键", "🟡 编辑分支存在但列表无入口（不可达）"],
         data=["petwise_announcements（双端共享键）"],
         exits=["App 首页展示"]),
    dict(id="admin-feedback", group="管理端", name="用户反馈 Feedback", route="/feedback", status="done",
         entry=["侧栏菜单（徽章真实计数）"],
         steps=[("读取反馈", "来自 App「我的→意见反馈」"),
                ("类型标签", "bug 问题 / suggestion 建议 / other 其他"),
                ("筛选", "全部 / 待处理（真实计数）/ 已处理"),
                ("标记已处理", "state=resolved，徽标同步减少")],
         branches=["⬜ 无回复用户 / 删除 / 重新打开"],
         data=["petwise_feedbacks（双端共享键）"],
         exits=["—"]),
    dict(id="admin-settings", group="管理端", name="系统设置 Settings", route="/settings", status="demo",
         entry=["侧栏菜单"],
         steps=[("模型与服务", "置信度阈值 0.6（0.5/0.6/0.7）"),
                ("LLM 选择", "GLM-4V 图文 / GLM-4 文本"),
                ("合规开关", "医疗免责 true / 新用户注册 true"),
                ("敏感词库", "增删词条（默认 4 词）"),
                ("管理员角色", "静态表 ⬜ 不可编辑")],
         branches=["⚠ cfg 与 words 无任何业务消费方（自读自写孤岛）", "既不影响 vision 阈值，也不参与审核"],
         data=["petwise_admin_cfg", "petwise_admin_words"],
         exits=["—"]),
]


def nav_svg() -> str:
    """全局导航图：C 端 / 管理端 / 数据与服务 三栏 + 主要跳转。"""
    groups = {
        "启动登录": ["Splash", "Login"],
        "首页与识别": ["Home", "Recognize", "BreedDetail"],
        "问诊主线": ["ConsultHub", "Consult(AI)", "PreConsult", "Doctors", "DoctorDetail", "ConsultationRoom", "Report", "Records"],
        "社区与消息": ["Community", "ChatList", "ChatRoom"],
        "我的": ["PetProfile", "Schedule", "Favorites", "Profile"],
    }
    admin = ["Login", "Dashboard", "Users", "Records", "Moderation", "Consults", "Announce", "Feedback", "Settings"]
    H = 700
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="\'PingFang SC\',\'Microsoft YaHei\',system-ui,sans-serif">',
             f'<rect width="{W}" height="{H}" rx="14" fill="{C["bg"]}"/>',
             f'<text x="24" y="34" font-size="17" font-weight="700" fill="{C["ink"]}">全局导航总览</text>',
             f'<text x="24" y="52" font-size="11.5" fill="{C["faint"]}">C 端 21 条路由 · 管理端 9 页 · 数据经 localStorage 共享键跨端闭环</text>']
    y = 70
    for gname, items in groups.items():
        parts.append(f'<text x="24" y="{y + 12}" font-size="12" font-weight="700" fill="{C["pine"]}">{esc(gname)}</text>')
        x = 130
        for it in items:
            wpx = int(text_w(it, 11.5)) + 22
            parts.append(f'<rect x="{x}" y="{y}" rx="9" width="{wpx}" height="24" fill="{C["card"]}" stroke="{C["line"]}"/>'
                         f'<text x="{x + wpx / 2}" y="{y + 16}" text-anchor="middle" font-size="11.5" fill="{C["ink"]}">{esc(it)}</text>')
            x += wpx + 10
            if x > W - 160:
                x, y = 130, y + 30
        y += 44
    parts.append(f'<line x1="24" y1="{y}" x2="{W - 24}" y2="{y}" stroke="{C["line"]}" stroke-dasharray="3 4"/>')
    y += 22
    parts.append(f'<text x="24" y="{y + 12}" font-size="12" font-weight="700" fill="{C["coral"]}">管理端（apps/admin）</text>')
    x = 150
    for it in admin:
        wpx = int(text_w(it, 11.5)) + 22
        parts.append(f'<rect x="{x}" y="{y}" rx="9" width="{wpx}" height="24" fill="{C["coral_soft"]}" stroke="{C["coral"]}" stroke-opacity=".3"/>'
                     f'<text x="{x + wpx / 2}" y="{y + 16}" text-anchor="middle" font-size="11.5" fill="{C["ink"]}">{esc(it)}</text>')
        x += wpx + 10
        if x > W - 160:
            x, y = 150, y + 30
    y += 46
    parts.append(f'<line x1="24" y1="{y}" x2="{W - 24}" y2="{y}" stroke="{C["line"]}" stroke-dasharray="3 4"/>')
    y += 22
    data_rows = [
        ("localStorage 共享键（双端闭环）", ["petwise_announcements ✅", "petwise_feedbacks ✅", "petwise_ann_dismissed"]),
        ("后端服务", ["services/vision（ONNX 推理）", "services/agent（LangGraph）", "services/api（网关）"]),
    ]
    for label, items in data_rows:
        parts.append(f'<text x="24" y="{y + 12}" font-size="12" font-weight="700" fill="{C["sub"]}">{esc(label)}</text>')
        y += 24
        s, ey = chip_row(24, y, items, C["grey_soft"], C["ink"], max_w=W - 60)
        parts.append(s)
        y = ey + 14
    return "\n".join(parts) + "\n</svg>"


def build_html(svg_map: dict[str, str]) -> str:
    """总览 HTML：目录 + 每页 SVG + 改进方向笔记区（localStorage 持久化）。"""
    toc, sections = [], []
    last_group = None
    for p in PAGES:
        if p["group"] != last_group:
            toc.append(f'<div class="toc-group">{esc(p["group"])}</div>')
            last_group = p["group"]
        toc.append(f'<a class="toc-item" href="#{p["id"]}">{esc(p["name"])}</a>')
        label, fg, bg = STATUS[p["status"]]
        steps_html = "".join(
            f'<li><b>{esc(s[0])}</b><span>{esc(s[1] if len(s) > 1 else "")}</span></li>' for s in p["steps"]
        )
        sections.append(f"""
<section id="{p['id']}" class="page">
  <div class="head">
    <h2>{esc(p['name'])} <code>{esc(p['route'])}</code>
      <span class="badge" style="color:{fg};background:{bg}">{esc(label)}</span></h2>
  </div>
  <div class="fig">{svg_map[p['id']]}</div>
  <details class="meta"><summary>流程步骤与数据源</summary>
    <ol>{steps_html}</ol>
    <p class="kv"><b>入口</b>{esc(' / '.join(p['entry']))}</p>
    <p class="kv"><b>数据源</b>{esc(' / '.join(p['data']))}</p>
    <p class="kv"><b>出口</b>{esc(' / '.join(p['exits']))}</p>
  </details>
  <div class="note">
    <div class="note-title">改进方向（点击填写，自动保存到服务器）<span class="save-state"></span></div>
    <div class="note-body" contenteditable="true" data-key="design-note-{p['id']}"></div>
  </div>
</section>""")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PetWise 设计文档 · 页面流程图</title>
<style>
  :root {{ --bg:#F4F1EA; --card:#FFF; --ink:#1F2E26; --sub:#5C6B62; --line:rgba(31,46,38,.12); --pine:#3E6B57; --coral:#C96A4A; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.7 'PingFang SC','Microsoft YaHei',system-ui,sans-serif; }}
  .wrap {{ display:grid; grid-template-columns:230px 1fr; gap:28px; max-width:1180px; margin:0 auto; padding:28px 20px 80px; }}
  aside {{ position:sticky; top:20px; align-self:start; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; max-height:calc(100vh - 40px); overflow:auto; }}
  .toc-group {{ font-size:12px; font-weight:700; color:var(--pine); margin:12px 0 6px; }}
  .toc-item {{ display:block; padding:4px 8px; border-radius:8px; color:var(--sub); text-decoration:none; font-size:13px; }}
  .toc-item:hover {{ background:#EAF1EC; color:var(--ink); }}
  header h1 {{ font-size:24px; margin:0 0 6px; }}
  header p {{ color:var(--sub); margin:0 0 8px; }}
  .save-hint {{ font-size:12.5px; color:var(--pine); background:var(--pine-soft,#EAF1EC); border:1px solid rgba(62,107,87,.25); border-radius:9px; padding:6px 12px; margin:6px 0 10px; }}
  .save-hint code {{ background:rgba(31,46,38,.06); padding:1px 6px; border-radius:6px; font-size:11.5px; }}
  .tools button {{ border:1px solid var(--line); background:var(--card); border-radius:9px; padding:6px 12px; font-size:12.5px; color:var(--sub); cursor:pointer; margin-right:8px; }}
  .tools button:hover {{ color:var(--pine); border-color:var(--pine); }}
  .page {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; margin:18px 0; }}
  .head h2 {{ font-size:18px; margin:0 0 12px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
  .head code {{ font-size:12px; color:var(--sub); background:#F1EFE8; padding:2px 8px; border-radius:7px; }}
  .badge {{ font-size:11.5px; font-weight:600; padding:2px 10px; border-radius:11px; }}
  .fig svg {{ width:100%; height:auto; display:block; }}
  details.meta {{ margin:10px 0; border-top:1px dashed var(--line); padding-top:10px; }}
  details.meta summary {{ cursor:pointer; font-size:13px; font-weight:600; color:var(--pine); }}
  details.meta ol {{ margin:8px 0 8px 20px; padding:0; }}
  details.meta li {{ font-size:13px; margin:3px 0; }}
  details.meta li span {{ color:var(--sub); margin-left:8px; font-size:12.5px; }}
  .kv {{ font-size:12.5px; margin:3px 0; }} .kv b {{ color:var(--pine); margin-right:8px; font-size:12px; }}
  .note {{ margin-top:10px; }}
  .note-title {{ font-size:12px; font-weight:700; color:var(--coral); margin-bottom:6px; display:flex; align-items:center; gap:8px; }}
  .save-state {{ font-size:11px; font-weight:400; color:var(--faint); }}
  .save-state.ok {{ color:var(--pine); }}
  .note-body {{ min-height:56px; border:1px dashed var(--line); border-radius:10px; padding:10px 12px; font-size:13.5px; background:#FCFBF7; outline:none; }}
  .note-body:focus {{ border-color:var(--coral); background:#FFF; }}
  @media print {{ aside,.tools,.note-title {{ display:none; }} .page {{ break-inside:avoid; }} }}
</style>
</head>
<body>
<div class="wrap">
<aside>
  <div class="toc-group">目录</div>
  {''.join(toc)}
</aside>
<main>
<header>
  <h1>PetWise 设计文档 · 页面流程图</h1>
  <p>共 {len(PAGES)} 个页面（C 端 20 + 管理端 9）。每张图含：入口 / 流程 / 分支规则 / 数据源 / 出口。状态：已实现 / 演示实现 / 占位。</p>
  <p class="save-hint">💾 改进方向<b>自动保存到服务器</b>（<code>docs/design/notes.json</code>），刷新 / 重开 / 换端口都不丢失。</p>
  <div class="tools">
    <button onclick="exportNotes()">导出全部改进方向（JSON）</button>
    <button onclick="window.print()">打印 / 存 PDF</button>
  </div>
</header>
{''.join(sections)}
</main>
</div>
<script>
  const K = k => 'design-note-' + k;
  const els = [...document.querySelectorAll('.note-body')];
  let apiOK = true;

  // 1) 优先从服务器拉取（notes.json 落盘，与端口/浏览器无关）
  fetch('/api/notes').then(r => r.json()).then(data => {{
    els.forEach(el => {{
      const v = data[el.dataset.key.replace('design-note-', '')];
      if (v) el.textContent = v;
    }});
  }}).catch(() => {{ apiOK = false; }});

  // 2) 输入即保存：POST 到服务器（debounce 400ms），localStorage 仅作离线兜底
  const pending = new Map();
  let timer = null;
  els.forEach(el => {{
    const key = el.dataset.key.replace('design-note-', '');
    const state = el.parentElement.querySelector('.save-state');
    const local = localStorage.getItem(K(key));
    if (local && !el.textContent) el.textContent = local;   // 服务器无此条时回填历史
    el.addEventListener('input', () => {{
      localStorage.setItem(K(key), el.innerText);           // 离线兜底
      pending.set(key, el.innerText);
      if (state) state.textContent = '保存中…', state.className = 'save-state';
      clearTimeout(timer);
      timer = setTimeout(flush, 400);
    }});
  }});

  function flush() {{
    if (!pending.size) return;
    const body = Object.fromEntries(pending);
    pending.clear();
    fetch('/api/notes', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(body),
    }}).then(r => r.json()).then(() => {{
      document.querySelectorAll('.note-body').forEach(el => {{
        const s = el.parentElement.querySelector('.save-state');
        if (s && el.innerText.trim()) s.textContent = '✓ 已保存', s.className = 'save-state ok';
      }});
    }}).catch(() => {{
      document.querySelectorAll('.note-body').forEach(el => {{
        const s = el.parentElement.querySelector('.save-state');
        if (s && el.innerText.trim()) s.textContent = '⚠ 仅保存在本机', s.className = 'save-state';
      }});
    }});
  }}
  window.addEventListener('beforeunload', flush);

  function exportNotes() {{
    const out = {{}};
    els.forEach(el => {{
      const t = el.innerText.trim();
      if (t) out[el.dataset.key.replace('design-note-','')] = t;
    }});
    const blob = new Blob([JSON.stringify(out, null, 2)], {{type:'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'design-improvements.json';
    a.click();
  }}
</script>
</body>
</html>"""


def main():
    FLOWS.mkdir(parents=True, exist_ok=True)
    svg_map = {}
    for p in PAGES:
        svg = page_svg(p)
        svg_map[p["id"]] = svg
        (FLOWS / f"{p['id']}.svg").write_text(svg, encoding="utf-8")
    (FLOWS / "global-nav.svg").write_text(nav_svg(), encoding="utf-8")
    svg_map["global-nav"] = (FLOWS / "global-nav.svg").read_text(encoding="utf-8")
    (OUT / "index.html").write_text(build_html(svg_map), encoding="utf-8")
    print(f"生成 {len(PAGES) + 1} 张 SVG → {FLOWS}")
    print(f"总览文档 → {OUT / 'index.html'}")


if __name__ == "__main__":
    main()
