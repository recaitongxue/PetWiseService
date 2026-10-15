/**
 * useAsync —— 把同步 mock 数据层平滑迁移到异步后端接口的最小组合式。
 *
 * 用法：
 *   const { data, loading, error, reload } = useAsync(() => petsApi.list())
 * 组件模板里直接用 data.value（可能为 null，记得给空态）。
 */
import { ref, onMounted } from 'vue'

export function useAsync(fn, { immediate = true } = {}) {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function run() {
    loading.value = true
    error.value = null
    try {
      data.value = await fn()
    } catch (e) {
      error.value = e
      // 不吞掉错误，便于页面按 ApiError.code 处理（如 20003 跳转登录）
    } finally {
      loading.value = false
    }
    return data.value
  }

  if (immediate) onMounted(run)

  return { data, loading, error, reload: run }
}
