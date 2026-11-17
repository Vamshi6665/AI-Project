import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, Vite proxies /api to FastAPI so the browser sees one origin (same as nginx in prod).
export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 800 },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: process.env.VITE_API_PROXY || 'http://localhost:8000', changeOrigin: true },
    },
  },
})
