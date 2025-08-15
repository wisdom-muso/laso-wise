import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    'import.meta.env.VITE_API_BASE': JSON.stringify(process.env.VITE_API_BASE || 'http://localhost:8005'),
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/doctors': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/accounts': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/patients': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/vitals': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://web:8005',
        changeOrigin: true,
      },
    },
  },
})



