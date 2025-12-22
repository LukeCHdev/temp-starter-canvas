import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { translations } from './translations';

// Transform the nested translation object into i18next format
const transformTranslations = () => {
  const resources = {
    en: { translation: {} },
    it: { translation: {} },
    fr: { translation: {} },
    es: { translation: {} },
    de: { translation: {} }
  };

  const processObject = (obj, path = '') => {
    for (const key in obj) {
      const value = obj[key];
      const newPath = path ? `${path}.${key}` : key;
      
      if (value && typeof value === 'object') {
        // Check if this is a translation object (has language keys)
        if ('en' in value && typeof value.en === 'string') {
          // This is a translation leaf node
          resources.en.translation[newPath] = value.en;
          resources.it.translation[newPath] = value.it || value.en;
          resources.fr.translation[newPath] = value.fr || value.en;
          resources.es.translation[newPath] = value.es || value.en;
          resources.de.translation[newPath] = value.de || value.en;
        } else {
          // This is a nested object, recurse
          processObject(value, newPath);
        }
      }
    }
  };

  processObject(translations);
  return resources;
};

const resources = transformTranslations();

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    supportedLngs: ['en', 'it', 'fr', 'es', 'de'],
    interpolation: {
      escapeValue: false
    },
    detection: {
      // URL path takes precedence - this ensures language from route is used first
      order: ['path', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'preferred_language',
      lookupFromPathIndex: 0  // Look at first path segment for language
    },
    react: {
      useSuspense: false
    }
  });

export default i18n;
