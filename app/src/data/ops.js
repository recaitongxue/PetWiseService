// App 端公告 / 反馈演示数据层：与管理端共用 localStorage 键
// 接入后端后整体替换为 API 调用
const ANN_KEY = 'petwise_announcements'
const FB_KEY = 'petwise_feedbacks'
const DISMISS_KEY = 'petwise_ann_dismissed'

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

export function submitFeedback({ user, type, text }) {
  const rows = readList(FB_KEY, [])
  const now = new Date()
  const time = `${now.toISOString().slice(0, 10)} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  rows.unshift({ id: 'f' + Date.now(), user, type, text, time, state: 'open' })
  localStorage.setItem(FB_KEY, JSON.stringify(rows))
}
