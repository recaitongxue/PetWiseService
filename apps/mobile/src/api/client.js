/**
 * 纯客户端助手（无后端对应的本地能力）
 * ------------------------------------------------------------------
 * 迁移说明：原 data/ops.js 里既有「本地 localStorage 逻辑」也有「应走后端的能力」。
 * 这里只保留确实没有后端接口的客户端能力：
 *   - 短信验证码每日发送频控（后端未提供计数接口，前端按日本地记）
 *   - 登录态判断
 * 钱包流水 / 问诊评价等业务数据一律走 @/api/* 真实接口。
 */
import { getAuth, getCachedUser, clearAuth } from '@shared/token'

export const SMS_DAILY_MAX = 10

function _todayKey() {
  return new Date().toISOString().slice(0, 10)
}

/** 今日已发送次数（按手机号分桶） */
export function smsSendCount(phone) {
  try {
    const raw = localStorage.getItem('petwise_sms_sent')
    const map = raw ? JSON.parse(raw) : {}
    const k = `${_todayKey()}:${phone || ''}`
    return map[k] || 0
  } catch {
    return 0
  }
}

/** 发送成功后 +1，返回最新次数 */
export function bumpSmsSend(phone) {
  try {
    const raw = localStorage.getItem('petwise_sms_sent')
    const map = raw ? JSON.parse(raw) : {}
    const k = `${_todayKey()}:${phone || ''}`
    map[k] = (map[k] || 0) + 1
    localStorage.setItem('petwise_sms_sent', JSON.stringify(map))
    return map[k]
  } catch {
    return 0
  }
}

/** 是否已登录（有 accessToken 即视为已登录） */
export function isAuthed() {
  return !!getAuth()?.accessToken
}

export { clearAuth, getCachedUser }
