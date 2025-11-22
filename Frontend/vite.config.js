import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  
  // 👇 Base path for GitHub Pages (keep as-is)
  base: process.env.VITE_BASE_PATH || "/Edu-bot",  // Must match your repo name

  // 👇 Add a proxy so Vite can talk to FastAPI during development
  server: {
    port: 5173,
    proxy: {
      // Your backend FastAPI runs on port 8000
      '/chat': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Optional: if you have other endpoints
      '/ping': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
})
