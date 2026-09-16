import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE_URL || 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // Proxy /api/* to the FastAPI backend during development so that
        // fetch('/api/health') works without CORS issues in the browser.
        '/api': {
          target: apiBase,
          changeOrigin: true,
        },
      },
    },
  }
})
