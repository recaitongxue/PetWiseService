/**
 * 令牌存储与刷新
 * ------------------------------------------------------------------
 * 登录态保存 accessToken / refreshToken 到 localStorage，并负责无感续期。
 * 本文件为 apps/mobile 与 apps/admin 共享实现（packages/shared）。
 */
const ACCESS_KEY = 'petwise_access_token'
const REFRESH_KEY = 'petwise_refresh_token'
const USER_KEY = 'petwise_user'

export function getAuth() {
  try {
    const raw = localStorage.getItem(ACCESS_KEY)
    if (!raw) return null
    return { accessToken: raw }
  } catch {
    return null
  }
}

export function getRefreshToken() {
  try {
    return localStorage.getItem(REFRESH_KEY)
  } catch {
    return null
  }
}

export function setTokens({ accessToken, refreshToken, user }) {
  try {
    if (accessToken) localStorage.setItem(ACCESS_KEY, accessToken)
    if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken)
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch {
    /* 隐私模式下降级为内存态 */
  }
}

export function setAuth(auth) {
  setTokens({ accessToken: auth?.accessToken, refreshToken: auth?.refreshToken, user: auth?.user })
}

export function clearAuth() {
  ;[ACCESS_KEY, REFRESH_KEY, USER_KEY].forEach((k) => {
    try {
      localStorage.removeItem(k)
    } catch {
      /* noop */
    }
  })
}

export function getCachedUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

/** 刷新令牌：并发请求会共用同一个 Promise（request.js 中做了单飞） */
export async function refresh() {
  const token = getRefreshToken()
  if (!token) return false
  const res = await fetch(`${(import.meta.env.VITE_API_BASE || '/api/v1').replace(/\/$/, '')}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken: token })
  })
  const json = await res.json().catch(() => ({}))
  if (json.code === 0 && json.data?.accessToken) {
    setTokens({
      accessToken: json.data.accessToken,
      refreshToken: json.data.refreshToken || token
    })
    return true
  }
  return false
}
