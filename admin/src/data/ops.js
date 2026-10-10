// 公告与反馈的演示数据层：localStorage 持久化，与 App 端共用同一存储键
// 接入后端后整体替换为 API 调用
const ANN_KEY = 'petwise_announcements'
const FB_KEY = 'petwise_feedbacks'

export const seedAnnouncements = [
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

export const seedFeedbacks = [
  {
    id: 'f1',
    user: '林小满',
    type: 'suggestion',
    text: '希望识别结果能直接跳转品种介绍，省得自己再搜。',
    time: '2026-10-09 14:22',
    state: 'open'
  },
  {
    id: 'f2',
    user: '陈屿',
    type: 'bug',
    text: '柯基照片在暗光下偶尔识别成柴犬，建议提升夜间样本。',
    time: '2026-10-07 21:05',
    state: 'open'
  }
]

function read(key, seed) {
  try {
    const raw = localStorage.getItem(key)
    if (raw) return JSON.parse(raw)
  } catch (e) { /* fallthrough */ }
  localStorage.setItem(key, JSON.stringify(seed))
  return seed.map((x) => ({ ...x }))
}

function write(key, rows) {
  localStorage.setItem(key, JSON.stringify(rows))
}

export const loadAnnouncements = () => read(ANN_KEY, seedAnnouncements)
export const saveAnnouncements = (rows) => write(ANN_KEY, rows)

export const loadFeedbacks = () => read(FB_KEY, seedFeedbacks)
export const saveFeedbacks = (rows) => write(FB_KEY, rows)

export function addFeedback(item) {
  const rows = loadFeedbacks()
  rows.unshift(item)
  saveFeedbacks(rows)
}
