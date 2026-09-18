import path from 'path'
import react from '@vitejs/plugin-react'
import lostCss from 'lost'
import postCssApply from 'postcss-apply'
import postColorModFunction from 'postcss-color-mod-function'
import postCssImport from 'postcss-import'
import postCssPresetEnv from 'postcss-preset-env'
import { defineConfig } from 'vite'

import { cssModuleSideEffect } from './vite-plugins/cssModuleSideEffect'

export default defineConfig({
  base: '',
  build: { outDir: 'dist' },
  plugins: [
    react({
      include: '**/*.tsx',
      babel: { configFile: true },
    }),
    cssModuleSideEffect(),
  ],
  optimizeDeps: {
    esbuildOptions: { target: 'es2020' },
  },
  css: {
    postcss: {
      plugins: [
        postCssImport({ root: 'src/' }),
        postCssApply(),
        postColorModFunction(),
        postCssPresetEnv({ stage: 0 }),
        lostCss(),
      ],
    },
  },
  define: {
    global: 'globalThis',
    _NODE_ENV_: JSON.stringify(process.env.NODE_ENV),
    process: { env: { NODE_ENV: JSON.stringify(process.env.NODE_ENV) } },
  },
  server: {
    port: 5177,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8765', changeOrigin: true },
      '/health': { target: 'http://127.0.0.1:8765', changeOrigin: true },
    },
  },
  resolve: {
    alias: {
      '@opentrons/components/styles/global': path.resolve(
        '../../components/src/styles/global.css'
      ),
      '@opentrons/components': path.resolve('../../components/src/index.ts'),
      '@opentrons/shared-data': path.resolve('../../shared-data/js/index.ts'),
      '@opentrons/step-generation': path.resolve(
        '../../step-generation/src/index.ts'
      ),
      i18next: path.resolve('./node_modules/i18next'),
      'react-i18next': path.resolve('./node_modules/react-i18next'),
    },
  },
})
