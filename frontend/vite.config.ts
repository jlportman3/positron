import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy target: use env var for Docker, fallback for local dev
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8005'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    allowedHosts: true,
    port: 3000,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            console.log(`[Proxy] ${req.method} ${req.url} -> ${proxyReq.path}`)
          })
          proxy.on('proxyRes', (proxyRes, req) => {
            console.log(`[Proxy] Response: ${proxyRes.statusCode} for ${req.url}`)
          })
          proxy.on('error', (err, req) => {
            console.error(`[Proxy Error] ${req.url}:`, err.message)
          })
        },
      },
    },
  },
})
