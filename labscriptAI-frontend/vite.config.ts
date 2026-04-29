<<<<<<< HEAD
import path from 'path';
=======
>>>>>>> upstream/main
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
<<<<<<< HEAD
  envDir: '..',
=======
>>>>>>> upstream/main
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
<<<<<<< HEAD
  define: {
    global: 'globalThis',
    _NODE_ENV_: JSON.stringify(process.env.NODE_ENV),
    process: { env: { NODE_ENV: JSON.stringify(process.env.NODE_ENV) } },
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
    },
    fs: {
      allow: ['..'],
    },
  },
  resolve: {
    alias: {
      '@opentrons/components/styles/global': path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/components/src/styles/global.css'
      ),
      '@opentrons/components': path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/components/src/index.ts'
      ),
      '@opentrons/shared-data': path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/shared-data/js/index.ts'
      ),
      '@opentrons/step-generation': path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/step-generation/src/index.ts'
      ),
      i18next: path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/node_modules/i18next'
      ),
      'react-i18next': path.resolve(
        '../web/opentrons-protocol-visualizer-web-slim/protocol-visualizer-web/client/node_modules/react-i18next'
      ),
    },
=======
  server: {
    host: '0.0.0.0', // 监听所有网络接口
    port: 5173,      // 明确设置端口
>>>>>>> upstream/main
  },
});
