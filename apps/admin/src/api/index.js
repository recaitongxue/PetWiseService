/**
 * 管理端 API 集合 —— 与后端 services/api/app/api/routers/admin.py 一一对应。
 *
 * 所有 /admin/* 接口要求 role=admin：用管理员手机号（演示 13900000000）
 * 走验证码登录后，token 里带 admin 角色，非管理员会被拦成 20004。
 *
 * 用法：
 *   import { adminApi } from '@/api'
 *   const stats = await adminApi.overview()
 */
import { http } from '@shared/request'

/* ---------------- 登录 ---------------- */
export const authApi = {
  sendCode: (phone, scene = 'login') => http.post('/auth/verification-codes', { phone, scene }),
  login: (payload) => http.post('/auth/login', payload),
  logout: () => http.post('/auth/logout'),
  me: () => http.get('/users/me')
}

/* ---------------- 管理端 ---------------- */
export const adminApi = {
  // 总览看板
  overview: () => http.get('/admin/overview'),

  // 公告
  announcements: (params) => http.get('/admin/announcements', params),
  createAnnouncement: (body) => http.post('/admin/announcements', body),
  updateAnnouncement: (id, body) => http.patch(`/admin/announcements/${id}`, body),
  removeAnnouncement: (id) => http.del(`/admin/announcements/${id}`),

  // 用户反馈
  feedbacks: (state) => http.get('/admin/feedbacks', state ? { state } : undefined),
  handleFeedback: (id, body) => http.patch(`/admin/feedbacks/${id}`, body),

  // 用户管理
  users: (q) => http.get('/admin/users', q ? { q } : undefined),
  updateUser: (id, body) => http.patch(`/admin/users/${id}`, body),

  // 问诊单
  consults: (state) => http.get('/admin/consults', state ? { state } : undefined),

  // 识别记录与纠正审核
  records: (status) => http.get('/admin/records', status ? { status } : undefined),
  reviewRecord: (id, body) => http.patch(`/admin/records/${id}`, body),

  // 内容审核（帖子举报）
  reports: (status) => http.get('/admin/reports', status ? { status } : undefined),
  handleReport: (id, body) => http.patch(`/admin/reports/${id}`, body),

  // 平台设置
  settings: () => http.get('/admin/settings'),
  updateSettings: (patch) => http.put('/admin/settings', patch)
}

export { http, ApiError, isAuthError } from '@shared/request'
