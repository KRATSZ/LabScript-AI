import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const frontendNodeModules = path.resolve(__dirname, 'node_modules');
const fromFrontendNodeModules = (packageName: string): string =>
  path.join(frontendNodeModules, packageName);

// https://vitejs.dev/config/
export default defineConfig({
  envDir: '..',
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
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
        'https://labscriptai.cn',
        'https://backend.labscriptai.cn',
      ],
      credentials: true
    },
    fs: {
      allow: ['..'],
    },
  },
  base: './',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    minify: 'esbuild',
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
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
      '@popperjs/core': fromFrontendNodeModules('@popperjs/core'),
      '@react-spring/types': fromFrontendNodeModules('@react-spring/types'),
      '@react-spring/web': fromFrontendNodeModules('@react-spring/web'),
      ajv: fromFrontendNodeModules('ajv'),
      classnames: fromFrontendNodeModules('classnames'),
      clsx: fromFrontendNodeModules('clsx'),
      'core-js': fromFrontendNodeModules('core-js'),
      i18next: fromFrontendNodeModules('i18next'),
      immer: fromFrontendNodeModules('immer'),
      interactjs: fromFrontendNodeModules('interactjs'),
      lodash: fromFrontendNodeModules('lodash'),
      'path-browserify': fromFrontendNodeModules('path-browserify'),
      react: fromFrontendNodeModules('react'),
      'react-dom': fromFrontendNodeModules('react-dom'),
      'react-i18next': fromFrontendNodeModules('react-i18next'),
      'react-markdown': fromFrontendNodeModules('react-markdown'),
      'react-popper': fromFrontendNodeModules('react-popper'),
      'react-remove-scroll': fromFrontendNodeModules('react-remove-scroll'),
      'react-select': fromFrontendNodeModules('react-select'),
      'react-viewport-list': fromFrontendNodeModules('react-viewport-list'),
      redux: fromFrontendNodeModules('redux'),
      'styled-components': fromFrontendNodeModules('styled-components'),
      'uuid/v4': path.join(frontendNodeModules, 'uuid/v4.js'),
      uuid: fromFrontendNodeModules('uuid'),
    },
  },
});
