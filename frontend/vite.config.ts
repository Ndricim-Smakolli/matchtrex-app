import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    https: false,
    cors: true,
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://api.beyondleverage.com:9443',
        changeOrigin: true,
        secure: false,
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          'X-Forwarded-Host': 'localhost:5173',
        },
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  define: {
    __DEV__: true
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  build: {
    target: 'esnext'
  }
});