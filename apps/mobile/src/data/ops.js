// App 端公告 / 反馈演示数据层：与管理端共用 localStorage 键
// 接入后端后整体替换为 API 调用
const ANN_KEY = 'petwise_announcements'
const FB_KEY = 'petwise_feedbacks'
const DISMISS_KEY = 'petwise_ann_dismissed'
const SCHED_DONE_KEY = 'petwise_schedule_done'   // 已完成日程 id
const SCHED_CUSTOM_KEY = 'petwise_schedule_custom' // 用户自定义日程
const RECORD_KEY = 'petwise_pet_records'         // 用户录入的健康记录
const AUTH_KEY = 'petwise_auth'                  // 登录态（演示用，接入后端后改为 token）
const ORDER_KEY = 'petwise_consult_orders'       // 用户发起的真人问诊单
const QUOTA_KEY = 'petwise_ai_quota'             // AI 免费额度（按日计）
const RATING_KEY = 'petwise_doctor_ratings'      // 医生评价
const REPORT_KEY = 'petwise_consult_reports'     // 问诊报告（结构化预问诊 / 真人问诊产出）

// 兜底种子：管理端尚未发布过公告时展示
const fallbackAnnouncements = [
  {
    id: 'a1',
    title: '品种百科上线',
    body: '识别结果页新增「品种百科」入口，支持查看 6 个常见品种的性格、寿命与护理要点。',
    date: '2026-10-10',
    level: 'event',
    active: true
  },
  {
    id: 'a2',
    title: '社区规范提醒',
    body: '近期发现少量广告类内容，已加强敏感词初筛。请勿发布含联系方式或药品交易的信息。',
    date: '2026-10-08',
    level: 'warn',
    active: true
  }
]

function readList(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    if (raw) {
      const rows = JSON.parse(raw)
      if (Array.isArray(rows)) return rows
    }
  } catch (e) { /* fallthrough */ }
  return fallback.map((x) => ({ ...x }))
}

// 当前生效的公告（管理端 active 且未被用户关掉）
export function activeAnnouncements() {
  const rows = readList(ANN_KEY, fallbackAnnouncements)
  const dismissed = readList(DISMISS_KEY, [])
  return rows.filter((a) => a.active && !dismissed.includes(a.id))
}

export function dismissAnnouncement(id) {
  const dismissed = readList(DISMISS_KEY, [])
  if (!dismissed.includes(id)) dismissed.push(id)
  localStorage.setItem(DISMISS_KEY, JSON.stringify(dismissed))
}

/* ---------------- 登录态 ---------------- */

export function getAuth() {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    return null
  }
}

export function isAuthed() {
  return Boolean(getAuth() && getAuth().phone)
}

// 演示登录：仅记录手机号与登录时间；接后端后保存 token / 用户信息
export function login({ phone, mode }) {
  const auth = { phone, mode, time: Date.now() }
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth))
  return auth
}

export function logout() {
  localStorage.removeItem(AUTH_KEY)
}

/* ---------------- 日程：完成状态与自定义条目 ---------------- */

// 已完成（勾选）的日程 id 集合
export function doneScheduleIds() {
  return readList(SCHED_DONE_KEY, [])
}

export function toggleScheduleDone(id) {
  const rows = doneScheduleIds()
  const i = rows.indexOf(id)
  if (i >= 0) rows.splice(i, 1)
  else rows.push(id)
  localStorage.setItem(SCHED_DONE_KEY, JSON.stringify(rows))
  return i < 0 // true 表示本次是"标记完成"
}

// 用户自建日程
export function customScheduleItems() {
  return readList(SCHED_CUSTOM_KEY, [])
}

export function addScheduleItem(item) {
  const rows = customScheduleItems()
  rows.push({ ...item, id: 's' + Date.now(), custom: true })
  localStorage.setItem(SCHED_CUSTOM_KEY, JSON.stringify(rows))
}

export function removeScheduleItem(id) {
  const rows = customScheduleItems().filter((x) => x.id !== id)
  localStorage.setItem(SCHED_CUSTOM_KEY, JSON.stringify(rows))
}

export function updateScheduleItem(id, patch) {
  const rows = customScheduleItems().map((x) => (x.id === id ? { ...x, ...patch } : x))
  localStorage.setItem(SCHED_CUSTOM_KEY, JSON.stringify(rows))
}

/* ---------------- 备忘录：轻量速记，不强制日期 ---------------- */

const MEMO_KEY = 'petwise_memos'

export function customMemos() {
  return readList(MEMO_KEY, []).sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0) || b.createdAt - a.createdAt)
}

export function addMemo(text, petId) {
  const rows = readList(MEMO_KEY, [])
  rows.push({
    id: 'memo' + Date.now(),
    text: String(text || '').slice(0, 500),
    petId: petId || '',
    pinned: false,
    createdAt: Date.now()
  })
  localStorage.setItem(MEMO_KEY, JSON.stringify(rows))
}

export function removeMemo(id) {
  const rows = readList(MEMO_KEY, []).filter((x) => x.id !== id)
  localStorage.setItem(MEMO_KEY, JSON.stringify(rows))
}

export function toggleMemoPin(id) {
  const rows = readList(MEMO_KEY, []).map((x) => (x.id === id ? { ...x, pinned: !x.pinned } : x))
  localStorage.setItem(MEMO_KEY, JSON.stringify(rows))
}

/* ---------------- 社区：帖子举报（管理端内容审核读取同一键） ---------------- */

const POST_REPORT_KEY = 'petwise_post_reports'

export function postReports() {
  return readList(POST_REPORT_KEY, [])
}

// 举报一条动态：写入共享键，管理端「内容审核」页可见并处理
export function reportPost({ postId, author, reason, detail }) {
  const rows = postReports()
  const now = new Date()
  const time = `${now.toISOString().slice(0, 10)} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  rows.unshift({
    id: 'rp' + Date.now(),
    postId,
    author: author || '',
    reason,
    detail: String(detail || '').slice(0, 200),
    reporter: getAuth()?.phone || 'anonymous',
    time,
    state: 'pending'
  })
  localStorage.setItem(POST_REPORT_KEY, JSON.stringify(rows))
}

/* ---------------- 收藏：用户主动收藏（与内置演示收藏合并展示） ---------------- */

const FAV_KEY = 'petwise_favorites'

export function customFavorites() {
  return readList(FAV_KEY, [])
}

export function addFavorite(item) {
  const rows = customFavorites()
  if (rows.some((x) => x.id === item.id)) return false
  rows.unshift({ ...item, custom: true })
  localStorage.setItem(FAV_KEY, JSON.stringify(rows))
  return true
}

export function removeFavorite(id) {
  const rows = customFavorites().filter((x) => x.id !== id)
  localStorage.setItem(FAV_KEY, JSON.stringify(rows))
}

/* ---------------- 钱包：余额与明细（演示实现，接支付后替换） ---------------- */

const WALLET_KEY = 'petwise_wallet'

export function wallet() {
  try {
    const raw = localStorage.getItem(WALLET_KEY)
    if (raw) return JSON.parse(raw)
  } catch (e) { /* fallthrough */ }
  return { balance: 68.5, txns: [] }
}

function saveWallet(w) {
  localStorage.setItem(WALLET_KEY, JSON.stringify(w))
}

// 充值 / 提现：返回最新钱包；演示环境不接真实支付
export function walletTransact(amount, note) {
  const w = wallet()
  const now = new Date()
  const time = `${now.toISOString().slice(0, 10)} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  const delta = Number(amount) || 0
  if (delta === 0) return w
  w.balance = Math.round((w.balance + delta) * 100) / 100
  w.txns.unshift({
    id: 't' + Date.now(),
    type: delta > 0 ? 'recharge' : 'withdraw',
    amount: Math.abs(delta),
    note: note || (delta > 0 ? '余额充值' : '余额提现'),
    time
  })
  saveWallet(w)
  return w
}

/* ---------------- 健康记录：用户手动录入 ---------------- */

// kind: weight 体重 / diet 饮食 / symptom 症状 / care 护理
export function customRecords() {
  return readList(RECORD_KEY, [])
}

export function recordsOf(petId) {
  return customRecords().filter((r) => r.petId === petId)
}

export function addRecord(rec) {
  const rows = customRecords()
  rows.push({ ...rec, id: 'r' + Date.now() })
  localStorage.setItem(RECORD_KEY, JSON.stringify(rows))
}

export function removeRecord(id) {
  const rows = customRecords().filter((x) => x.id !== id)
  localStorage.setItem(RECORD_KEY, JSON.stringify(rows))
}

/* ---------------- 问诊：AI 免费额度 ---------------- */

const AI_DAILY_FREE = 3 // 每日免费次数（对齐主流平台的新手额度策略）

function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function readJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* 隐私模式下 localStorage 不可用时静默降级为内存态 */
  }
}

/** 剩余免费次数；跨天自动重置 */
export function aiQuota() {
  const q = readJSON(QUOTA_KEY, { date: '', used: 0 })
  if (q.date !== today()) return { date: today(), used: 0, free: AI_DAILY_FREE, left: AI_DAILY_FREE }
  return { ...q, free: AI_DAILY_FREE, left: Math.max(0, AI_DAILY_FREE - q.used) }
}

/** 消耗一次 AI 问诊额度 */
export function consumeAiQuota() {
  const q = readJSON(QUOTA_KEY, { date: '', used: 0 })
  const next = q.date === today() ? { date: today(), used: q.used + 1 } : { date: today(), used: 1 }
  writeJSON(QUOTA_KEY, next)
  return { ...next, free: AI_DAILY_FREE, left: Math.max(0, AI_DAILY_FREE - next.used) }
}

/* ---------------- 问诊：真人问诊单 ---------------- */

export function consultOrders() {
  return readJSON(ORDER_KEY, [])
}

export function orderById(id) {
  return consultOrders().find((o) => o.id === id) || null
}

/**
 * 创建真人问诊单。summary 为 AI 生成并可由用户编辑的病例摘要，
 * 这样医生接诊时不必重复追问（主流平台的核心效率点）。
 */
export function createConsultOrder({ doctorId, mode, petId, summary, price }) {
  const orders = consultOrders()
  const order = {
    id: `o${Date.now()}`,
    doctorId,
    mode,
    petId,
    summary,
    price,
    state: 'pending', // pending → replied → closed
    createdAt: new Date().toISOString(),
    messages: []
  }
  orders.unshift(order)
  writeJSON(ORDER_KEY, orders)
  return order
}

export function appendOrderMessage(id, msg) {
  const orders = consultOrders()
  const o = orders.find((x) => x.id === id)
  if (!o) return null
  o.messages.push(msg)
  writeJSON(ORDER_KEY, orders)
  return o
}

export function closeOrder(id) {
  const orders = consultOrders()
  const o = orders.find((x) => x.id === id)
  if (!o) return null
  o.state = 'closed'
  o.closedAt = new Date().toISOString()
  writeJSON(ORDER_KEY, orders)
  return o
}

/* ---------------- 问诊：医生评价 ---------------- */

export function doctorRatings() {
  return readJSON(RATING_KEY, {})
}

export function rateOrder(orderId, doctorId, score, tags = []) {
  const all = doctorRatings()
  all[orderId] = { doctorId, score, tags, at: new Date().toISOString() }
  writeJSON(RATING_KEY, all)
  return all[orderId]
}

/* ---------------- 问诊报告 ---------------- */

export function reports() {
  return readJSON(REPORT_KEY, [])
}

export function reportById(id) {
  return reports().find((r) => r.id === id) || null
}

/**
 * 保存问诊报告。报告是问诊模块的最终产出物：
 * 既能给用户带去线下医院看，也能回流进健康档案与日程。
 */
export function saveReport(report) {
  const rows = reports()
  const full = {
    id: 'rp' + Date.now(),
    createdAt: new Date().toISOString(),
    date: today(),
    archived: false, // 是否已写入宠物健康档案
    reminded: false, // 是否已生成用药/复查提醒
    ...report
  }
  rows.unshift(full)
  writeJSON(REPORT_KEY, rows)
  return full
}

/** 标记报告已回流到某处（archived 档案 / reminded 提醒），避免重复写入 */
export function markReport(id, field) {
  const rows = reports()
  const r = rows.find((x) => x.id === id)
  if (!r) return null
  r[field] = true
  writeJSON(REPORT_KEY, rows)
  return r
}

/**
 * 报告回流进宠物健康档案（复用健康记录存储，档案页时间轴立即可见）
 */
export function archiveReport(report, petId) {
  if (!report || report.archived) return false
  addRecord({
    petId,
    kind: 'symptom',
    date: report.date,
    value: null,
    note: `【问诊报告】${report.chief?.symptomLabels?.join('、') || report.title} — ${
      report.triage?.label || ''
    }。${report.triage?.advice || ''}`
  })
  markReport(report.id, 'archived')
  return true
}

/**
 * 把处方/复查计划转成日程提醒（复用日程存储，日程页立即可见）
 */
export function remindFromReport(report, petId) {
  if (!report || report.reminded) return 0
  const items = []

  if (report.rx?.drugs?.length) {
    items.push({
      type: 'other',
      title: `按处方用药：${report.rx.drugs.map((d) => d.name).join('、')}`,
      date: addDays(report.date, 1),
      petId
    })
  }
  items.push({
    type: 'check',
    title: report.triage?.level === 'home' ? '复查：症状是否缓解' : '复诊：按医生建议回访',
    date: addDays(report.date, report.triage?.level === 'home' ? 3 : 7),
    petId
  })

  items.forEach((it) => addScheduleItem(it))
  markReport(report.id, 'reminded')
  return items.length
}

function addDays(dateStr, n) {
  const d = new Date(dateStr)
  d.setDate(d.getDate() + n)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function submitFeedback({ user, type, text }) {
  const rows = readList(FB_KEY, [])
  const now = new Date()
  const time = `${now.toISOString().slice(0, 10)} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  rows.unshift({ id: 'f' + Date.now(), user, type, text, time, state: 'open' })
  localStorage.setItem(FB_KEY, JSON.stringify(rows))
}

/* ---------------- 识别记录：品种识别 + 手动纠正（管理端审核共用同一键） ----------------
 * status: done      正常识别完成（未纠正）
 *         review    用户手动纠正，待管理端审核
 *         approved  审核通过 → 可导出为训练数据集
 *         rejected  审核驳回 → 维持模型原预测
 */
const RECOG_KEY = 'petwise_recognitions'

export function recognitionHistory() {
  return readList(RECOG_KEY, [])
}

// 保存一次识别结果（predicted = 模型 top1）
export function saveRecognition({ species, predicted, confidence, alternatives, imageRef }) {
  const rows = recognitionHistory()
  const rec = {
    id: 'rc' + Date.now(),
    species,
    predicted,
    confidence: Number(confidence),
    alternatives: alternatives || [],
    corrected: null,
    status: 'done',
    imageRef: imageRef || '',
    time: new Date().toISOString()
  }
  rows.unshift(rec)
  localStorage.setItem(RECOG_KEY, JSON.stringify(rows.slice(0, 100)))
  return rec
}

// 用户认为识别不准 → 手动纠正，进入管理端审核队列
export function correctRecognition(id, breed) {
  const rows = recognitionHistory()
  const rec = rows.find((x) => x.id === id)
  if (!rec || rec.status !== 'done' || !breed) return null
  rec.corrected = breed
  rec.status = 'review'
  localStorage.setItem(RECOG_KEY, JSON.stringify(rows))
  return rec
}

// 审核通过的记录 → 训练数据集样本（管理端导出用）
export function approvedSamples() {
  return recognitionHistory().filter((r) => r.status === 'approved')
}

/* ============================================================
   账号管理（/account）：偏好、隐私、黑名单、注销
   ============================================================ */

const ACCOUNT_PREFS_KEY = 'petwise_account_prefs'
const BLACKLIST_KEY = 'petwise_blacklist'

// 隐私与推荐偏好（默认值参照主流 App：个性化推荐默认开、动态公开）
export function accountPrefs() {
  const fallback = {
    personalized: true,
    visibility: 'public', // public / followers / private
    binds: { wechat: true, apple: false }
  }
  return { ...fallback, ...readJSON(ACCOUNT_PREFS_KEY, {}) }
}

export function saveAccountPrefs(patch) {
  const next = { ...accountPrefs(), ...patch }
  localStorage.setItem(ACCOUNT_PREFS_KEY, JSON.stringify(next))
  return next
}

// 黑名单（演示种子：两位用户）
export function blacklist() {
  const seed = [
    { id: 'bl1', name: '广告号小达人', reason: '发布垃圾广告', time: '2026-09-21' },
    { id: 'bl2', name: '杠精本杠', reason: '辱骂攻击他人', time: '2026-10-02' }
  ]
  return readJSON(BLACKLIST_KEY, seed)
}

export function unblockUser(id) {
  const rows = blacklist().filter((u) => u.id !== id)
  localStorage.setItem(BLACKLIST_KEY, JSON.stringify(rows))
  return rows
}

// 清除本机账号数据（注销演示用）：保留 auth 由调用方决定
export function clearLocalAccountData() {
  const removed = []
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const k = localStorage.key(i)
    if (k && k.startsWith('petwise_')) {
      removed.push(k)
      localStorage.removeItem(k)
    }
  }
  return removed
}

/* 验证码发送频控（按日计数）：Login 与账号管理共用一份实现 */
const SMS_SENT_KEY = 'petwise_sms_sent'
export const SMS_DAILY_MAX = 5

export function smsSendCount() {
  try {
    const raw = localStorage.getItem(SMS_SENT_KEY)
    if (!raw) return 0
    const data = JSON.parse(raw)
    const today = new Date().toISOString().slice(0, 10)
    return data.date === today ? data.count : 0
  } catch (e) {
    return 0
  }
}

export function bumpSmsSend() {
  const today = new Date().toISOString().slice(0, 10)
  const next = smsSendCount() + 1
  try {
    localStorage.setItem(SMS_SENT_KEY, JSON.stringify({ date: today, count: next }))
  } catch (e) { /* ignore */ }
  return next
}
