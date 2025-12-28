import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@smartbook/ui': path.resolve(__dirname, '../../packages/ui/src'),
      '@smartbook/api': path.resolve(__dirname, '../../packages/api/src'),
      '@smartbook/utils': path.resolve(__dirname, '../../packages/utils/src'),
      '@smartbook/types': path.resolve(__dirname, '../../packages/types/src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
