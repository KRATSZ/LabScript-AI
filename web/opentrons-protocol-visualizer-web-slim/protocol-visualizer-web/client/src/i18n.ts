import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import '../../../components/src/i18n'
import { shared_en_resources } from '../../../components/src/assets/localization/en'

import branded from './locales/en/branded.json'
import protocolVisualization from './locales/en/protocol_visualization.json'

const enResourceBundles = {
  ...shared_en_resources,
  protocol_visualization: protocolVisualization,
  branded,
}

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    lng: 'en',
    fallbackLng: 'en',
    keySeparator: false,
    saveMissing: true,
    interpolation: { escapeValue: false },
    ns: Object.keys(enResourceBundles),
    resources: {
      en: enResourceBundles,
    },
  })
} else {
  Object.entries(enResourceBundles).forEach(([namespace, resource]) => {
    i18n.addResourceBundle('en', namespace, resource, true, true)
  })
}

export { i18n }
