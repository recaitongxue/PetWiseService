import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 移动优先 + 哈希路由，便于 Capacitor 打包为 iOS / Android / Web 单代码库
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
    port: 5173,
    allowedHosts: true,
    // 允许 dev server 访问仓库根下的 packages/shared
    fs: { allow: [fileURLToPath(new URL('../..', import.meta.url))] },
    // 后端联调代理：本地起后端后，前端的 /api 请求转发过去，规避 CORS
    // 目标地址可用环境变量覆盖：VITE_PROXY_TARGET=http://localhost:8080
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8080',
        changeOrigin: true
      }
    }
    // 注意：不要硬编码 hmr.clientPort，否则本地开发的 HMR WebSocket 会连错端口
    // （反向代理部署时如需 wss，可在 nginx 层转发 /@vite/client 的 ws）
  },
  build: {
    target: 'es2018',
    chunkSizeWarningLimit: 1200
  }
})
