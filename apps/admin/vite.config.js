import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      // 共享基础层（request/token/toast/ToastHost）：packages/shared 唯一实现
      '@shared': fileURLToPath(new URL('../../packages/shared/src', import.meta.url))
    }
  },
  server: {
    host: true,
    port: 5174,
    allowedHosts: true,
    // 允许 dev server 访问仓库根下的 packages/shared
    fs: { allow: [fileURLToPath(new URL('../..', import.meta.url))] },
    // 后端联调代理：与 App 端一致，/api 转发到业务后端，规避 CORS
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})
