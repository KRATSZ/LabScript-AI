import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    host: '0.0.0.0', // 监听所有网络接口
    port: 5173,      // 明确设置端口
    cors: {
      origin: [
        'http://localhost:5173',
        'https://ai4ot.cn',
        'http://ai4ot.cn',
        'https://api.ai4ot.cn',
        'http://api.ai4ot.cn'
      ],
      credentials: true
    }
  },
});
