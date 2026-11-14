import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      input: {
        roomtour: fileURLToPath(new URL('./index.html', import.meta.url)),
        assignment3: fileURLToPath(new URL('./assignment3.html', import.meta.url)),
        assignment4: fileURLToPath(new URL('./assignment4.html', import.meta.url)),
      },
    },
  },
  server: {
    proxy: {
      '/api/assignment4': { target: 'http://127.0.0.1:8001', ws: true },
      '/api': 'http://localhost:8000',
    },
  },
})
