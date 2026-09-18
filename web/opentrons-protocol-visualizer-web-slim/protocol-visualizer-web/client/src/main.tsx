import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { I18nextProvider } from 'react-i18next'

import '@opentrons/components/styles/global'

import { App } from './App'
import { i18n } from './i18n'
import { RootErrorBoundary } from './RootErrorBoundary'

import './global.css'

const rootElement = document.getElementById('root')

if (rootElement != null) {
  ReactDOM.createRoot(rootElement).render(
    <StrictMode>
      <RootErrorBoundary>
        <I18nextProvider i18n={i18n}>
          <App />
        </I18nextProvider>
      </RootErrorBoundary>
    </StrictMode>
  )
} else {
  console.error('Root element not found')
}
