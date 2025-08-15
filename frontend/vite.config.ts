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
    'import.meta.env.VITE_API_BASE': JSON.stringify(process.env.VITE_API_BASE || ''),
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/doctors': {
        target: process.env.VITE_API_BASE || 'http://65.108.91.110:8005',
        changeOrigin: true,
      },
      '/accounts': {
        target: process.env.VITE_API_BASE || 'http://65.108.91.110:8005',
        changeOrigin: true,
      },
      '/patients': {
        target: process.env.VITE_API_BASE || 'http://65.108.91.110:8005',
        changeOrigin: true,
      },
      '/vitals': {
        target: process.env.VITE_API_BASE || 'http://65.108.91.110:8005',
        changeOrigin: true,
      },
      '/api': {
        target: process.env.VITE_API_BASE || 'http://65.108.91.110:8005',
        changeOrigin: true,
      },
    },
  },
})



