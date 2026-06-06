import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/auth':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/analysis': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/records':  { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/health':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/chat':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
