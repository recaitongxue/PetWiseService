// ============================================================
// Petwise · 轻提示（Toast）全局状态
// 任何组件可 import { showToast } 调用，由 ToastHost 统一渲染
// 本文件为 apps/mobile 与 apps/admin 共享实现（packages/shared）。
// ============================================================
import { reactive } from 'vue'

export const toasts = reactive([])
let seq = 0

export function showToast(message, opts = {}) {
  const id = ++seq
  toasts.push({ id, message, type: opts.type || 'default' })
  setTimeout(() => {
    const i = toasts.findIndex((t) => t.id === id)
    if (i !== -1) toasts.splice(i, 1)
  }, opts.duration || 2200)
}
