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
    port: 5173
  },
  build: {
    target: 'es2018',
    chunkSizeWarningLimit: 1200
  }
})
