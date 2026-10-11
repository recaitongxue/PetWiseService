import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 移动优先 + 哈希路由，便于 Capacitor 打包为 iOS / Android / Web 单代码库
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: true
    // 注意：不要硬编码 hmr.clientPort，否则本地开发的 HMR WebSocket 会连错端口
    // （反向代理部署时如需 wss，可在 nginx 层转发 /@vite/client 的 ws）
  },
  build: {
    target: 'es2018',
    chunkSizeWarningLimit: 1200
  }
})
