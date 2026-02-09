import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/stats': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/search': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/ask': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/agents': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/memory': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/bdgraph': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/cache': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/qa': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/pipeline': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/alerts': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/rag': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/agent': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/dify': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/collections': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/contacts': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/programs': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/jobs': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/ingest': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/sync': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/index': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/dashboard': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/documents': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/activities': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/analytics': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/ai': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/graph': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/notifications': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/webhooks': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/contracts': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/competitive': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/reports': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/ml': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/integrations': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/outreach': {
        target: 'http://127.0.0.1:8300',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
        ws: true,
      },
      '/sse': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/realtime': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/embeddings': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
      '/automation': {
        target: 'http://127.0.0.1:8100',
        changeOrigin: true,
      },
    },
  },
})
