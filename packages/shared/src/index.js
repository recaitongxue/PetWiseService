/**
 * packages/shared 桶文件：统一出口，避免各端引用散落到具体文件路径。
 */
export { http, ApiError, isAuthError } from './request'
export {
  getAuth,
  setAuth,
  clearAuth,
  setTokens,
  getRefreshToken,
  getCachedUser,
  refresh
} from './token'
export { toasts, showToast } from './toast'
