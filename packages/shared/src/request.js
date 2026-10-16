/**
 * 统一请求层（零依赖 fetch 封装）
 * ------------------------------------------------------------------
 * 对接《Petwise 服务端接口文档 v1.0》：
 * - 统一信封 { code, message, data, timestamp, traceId }，code=0 为成功
 * - 自动注入 Bearer token；token 过期（20002）时静默 refresh 后重试一次
 * - 抛出的 ApiError 携带业务 code，便于页面按分支处理
 *
 * 本文件为 apps/mobile 与 apps/admin 共享实现（packages/shared），
 * 修改后需两端构建验证。
 */
import { getAuth, setAuth, clearAuth, getRefreshToken, setTokens, refresh } from './token'

const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export class ApiError extends Error {
  constructor(code, message, data) {
    super(message || '请求失败')
    this.code = code
    this.data = data
    this.name = 'ApiError'
  }
}

/** 是否需要重新登录 */
export function isAuthError(err) {
  return err instanceof ApiError && [20001, 20003].includes(err.code)
}

/* ---------------- 核心请求 ---------------- */

let refreshing = null

async function rawFetch(path, { method = 'GET', body, query, headers = {}, raw = false } = {}) {
  const url = new URL(BASE.replace(/\/$/, '') + path, location.origin)
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }

  const init = { method, headers: { Accept: 'application/json', ...headers } }
  const auth = getAuth()
  if (auth?.accessToken) init.headers.Authorization = `Bearer ${auth.accessToken}`

  if (body instanceof FormData) {
    init.body = body // 上传场景由浏览器自动设置 Content-Type
  } else if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  const res = await fetch(url.toString(), init)
  const text = await res.text()

  if (raw) {
    // 文件导出等场景：返回原始响应
    if (!res.ok) throw new ApiError(res.status, '导出失败')
    return res
  }

  let json
  try {
    json = text ? JSON.parse(text) : {}
  } catch {
    throw new ApiError(-1, '响应格式错误')
  }

  // HTTP 层错误兜底
  if (!res.ok && json.code === undefined) throw new ApiError(res.status, `请求失败（${res.status}）`)

  return json
}

async function doRequest(path, options = {}, retry = true) {
  const json = await rawFetch(path, options)
  const { code = 0, message, data } = json

  if (code === 0) return data

  // token 过期：静默刷新后重试一次
  if (code === 20002 && retry) {
    if (!refreshing) {
      refreshing = refresh()
        .catch(() => null)
        .finally(() => {
          refreshing = null
        })
    }
    const ok = await refreshing
    if (ok) return doRequest(path, options, false)
    clearAuth()
    throw new ApiError(20003, '登录已过期，请重新登录')
  }

  throw new ApiError(code, message, data)
}

export const http = {
  get: (path, query, opts) => doRequest(path, { ...opts, method: 'GET', query }),
  post: (path, body, opts) => doRequest(path, { ...opts, method: 'POST', body }),
  patch: (path, body, opts) => doRequest(path, { ...opts, method: 'PATCH', body }),
  put: (path, body, opts) => doRequest(path, { ...opts, method: 'PUT', body }),
  del: (path, body, opts) => doRequest(path, { ...opts, method: 'DELETE', body }),
  upload: (path, formData, extra = {}) =>
    doRequest(path, { method: 'POST', body: formData, ...extra }),
  blob: (path) => rawFetch(path, { method: 'GET', raw: true })
}

export { getAuth, setAuth, clearAuth, setTokens, getRefreshToken }
