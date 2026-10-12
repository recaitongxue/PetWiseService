/**
 * API 接口集合 —— 路径与字段严格对应 docs/API.md
 * ------------------------------------------------------------------
 * 用法：
 *   import { authApi, petsApi, consultApi } from '@/api'
 *   const pets = await petsApi.list()
 *
 * 联调时把页面对 data/mock.js、data/ops.js 的调用替换为这里的函数即可，
 * 映射关系见 API.md「附录 B：Mock → API 替换映射表」。
 */
import { http } from './request'

/* ---------------- 认证与用户 ---------------- */
export const authApi = {
  sendCode: (phone, scene = 'login') => http.post('/auth/verification-codes', { phone, scene }),
  login: (payload) => http.post('/auth/login', payload),
  logout: () => http.post('/auth/logout'),
  me: () => http.get('/users/me'),
  updateMe: (patch) => http.patch('/users/me', patch)
}

/* ---------------- 宠物档案 ---------------- */
export const petsApi = {
  list: () => http.get('/pets'),
  detail: (id) => http.get(`/pets/${id}`),
  create: (body) => http.post('/pets', body),
  update: (id, body) => http.patch(`/pets/${id}`, body),
  remove: (id) => http.del(`/pets/${id}`),
  trend: (id, week) => http.get(`/pets/${id}/health-trend`, { week }),
  reminders: (id, date) => http.get(`/pets/${id}/reminders`, { date }),
  weights: (id, months = 6) => http.get(`/pets/${id}/weights`, { months }),
  addWeight: (id, body) => http.post(`/pets/${id}/weights`, body),
  records: (id, params) => http.get(`/pets/${id}/records`, params),
  addRecord: (id, body) => http.post(`/pets/${id}/records`, body),
  removeRecord: (recordId) => http.del(`/records/${recordId}`)
}

/* ---------------- 日程与提醒 ---------------- */
export const scheduleApi = {
  list: (params) => http.get('/schedule', params),
  types: () => http.get('/schedule/types'),
  create: (body) => http.post('/schedule', body),
  update: (id, body) => http.patch(`/schedule/${id}`, body),
  toggleDone: (id, done) => http.patch(`/schedule/${id}/done`, { done }),
  remove: (id) => http.del(`/schedule/${id}`)
}

/* ---------------- 首页聚合 ---------------- */
export const homeApi = {
  summary: (petId) => http.get('/home', { petId })
}

/* ---------------- 公告 · 反馈 · 品种 · 收藏 ---------------- */
export const contentApi = {
  announcements: (active = true) => http.get('/announcements', { active }),
  dismissAnnouncement: (id) => http.post(`/announcements/${id}/dismiss`),
  submitFeedback: (body) => http.post('/feedbacks', body),
  breeds: (params) => http.get('/breeds', params),
  breed: (id) => http.get(`/breeds/${id}`),
  favorites: (kind) => http.get('/favorites', { kind }),
  addFavorite: (kind, targetId) => http.post('/favorites', { kind, targetId }),
  removeFavorite: (kind, targetId) => http.del(`/favorites/${kind}/${targetId}`)
}

/* ---------------- 拍照识别 ---------------- */
export const recognitionApi = {
  recognize: (formData) => http.upload('/recognitions', formData),
  history: (params) => http.get('/recognitions', params),
  task: (taskId) => http.get(`/recognitions/tasks/${taskId}`)
}

/* ---------------- 在线问诊（核心模块） ---------------- */
export const consultApi = {
  // 元信息与词典
  dictionary: () => http.get('/consult/dictionary'),
  departments: () => http.get('/consult/departments'),
  modes: () => http.get('/consult/modes'),

  // AI 额度与分诊
  quota: () => http.get('/consult/ai-quota'),
  triage: (body) => http.post('/consult/triage', body),
  preConsult: (body) => http.post('/consult/pre-consult', body),
  caseSummary: (body) => http.post('/consult/case-summary', body),

  // 医生
  doctors: (params) => http.get('/doctors', params),
  doctor: (id) => http.get(`/doctors/${id}`),
  doctorReviews: (id, params) => http.get(`/doctors/${id}/reviews`, params),

  // 问诊单
  orders: (state) => http.get('/consult/orders', { state }),
  order: (id) => http.get(`/consult/orders/${id}`),
  createOrder: (body) => http.post('/consult/orders', body),
  messages: (id, params) => http.get(`/consult/orders/${id}/messages`, params),
  sendMessage: (id, body) => http.post(`/consult/orders/${id}/messages`, body),
  call: (id) => http.post(`/consult/orders/${id}/call`),
  close: (id) => http.post(`/consult/orders/${id}/close`),
  read: (id, lastMessageId) => http.post(`/consult/orders/${id}/read`, { lastMessageId }),
  rate: (id, body) => http.post(`/consult/orders/${id}/rating`, body),

  // 报告
  reports: (params) => http.get('/consult/reports', params),
  report: (id) => http.get(`/consult/reports/${id}`),
  saveReport: (body) => http.post('/consult/reports', body),
  archiveReport: (id) => http.post(`/consult/reports/${id}/archive`),
  remindReport: (id) => http.post(`/consult/reports/${id}/remind`),
  exportReport: (id, format = 'pdf') => http.blob(`/consult/reports/${id}/export?format=${format}`)
}

/* ---------------- 社区 ---------------- */
export const communityApi = {
  posts: (params) => http.get('/posts', params),
  publish: (body) => http.post('/posts', body),
  like: (id) => http.post(`/posts/${id}/like`),
  unlike: (id) => http.del(`/posts/${id}/like`),
  comments: (id, params) => http.get(`/posts/${id}/comments`, params),
  comment: (id, text) => http.post(`/posts/${id}/comments`, { text })
}

/* ---------------- 即时消息 ---------------- */
export const imApi = {
  conversations: () => http.get('/conversations'),
  messages: (id, params) => http.get(`/conversations/${id}/messages`, params),
  send: (id, body) => http.post(`/conversations/${id}/messages`, body),
  read: (id) => http.post(`/conversations/${id}/read`)
}

/* ---------------- 文件上传 ---------------- */
export const fileApi = {
  upload: (formData, scene = 'post') => {
    formData.append('scene', scene)
    return http.upload('/files', formData)
  }
}

/* ---------------- 管理端 ---------------- */
export const adminApi = {
  overview: () => http.get('/admin/overview'),
  announcements: (params) => http.get('/admin/announcements', params),
  createAnnouncement: (body) => http.post('/admin/announcements', body),
  updateAnnouncement: (id, body) => http.patch(`/admin/announcements/${id}`, body),
  removeAnnouncement: (id) => http.del(`/admin/announcements/${id}`),
  feedbacks: (state) => http.get('/admin/feedbacks', { state }),
  handleFeedback: (id, body) => http.patch(`/admin/feedbacks/${id}`, body)
}

export { http, ApiError, isAuthError, USE_MOCK } from './request'
