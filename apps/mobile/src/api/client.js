/**
 * 纯客户端助手（无后端对应的本地能力）
 * ------------------------------------------------------------------
 * 迁移说明：原 data/ops.js 里既有「本地 localStorage 逻辑」也有「应走后端的能力」。
 * 这里只保留确实没有后端接口的客户端能力：
 *   - 短信验证码每日发送频控（后端未提供计数接口，前端按日本地记）
 *   - 钱包交易流水展示（后端仅有余额，流水本地记）
 *   - 登录态判断
 * 其余能力已全部改为调用 @/api/* 真实接口。
 */
import { getAuth, getCachedUser, clearAuth } from './token'

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

/** 缓存的用户资料（用于无需请求的场景） */
export function cachedUser() {
  return getCachedUser()
}

/* ---------------- 钱包交易流水（本地展示） ---------------- */
const WALLET_KEY = 'petwise_wallet_tx'

export function walletTransactions() {
  try {
    const raw = localStorage.getItem(WALLET_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addWalletTransaction(tx) {
  const list = walletTransactions()
  list.unshift({ id: `tx${Date.now()}`, date: new Date().toISOString().slice(0, 10), ...tx })
  try {
    localStorage.setItem(WALLET_KEY, JSON.stringify(list.slice(0, 50)))
  } catch {
    /* noop */
  }
  return list
}

export { clearAuth, getCachedUser }
