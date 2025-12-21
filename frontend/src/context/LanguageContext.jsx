import React, { createContext, useContext, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const LanguageContext = createContext(null);

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error('useLanguage must be used within LanguageProvider');
    }
    return context;
};

// Supported languages
export const SUPPORTED_LANGUAGES = {
    'en': { code: 'en', name: 'English', flag: '🇬🇧' },
    'it': { code: 'it', name: 'Italiano', flag: '🇮🇹' },
    'es': { code: 'es', name: 'Español', flag: '🇪🇸' },
    'fr': { code: 'fr', name: 'Français', flag: '🇫🇷' },
    'de': { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
};

export const LanguageProvider = ({ children }) => {
    const { i18n } = useTranslation();
    
    // Get initial language from i18next (which uses detector)
    const [language, setLanguage] = useState(i18n.language?.split('-')[0] || 'en');

    const changeLanguage = (langCode) => {
        if (SUPPORTED_LANGUAGES[langCode]) {
            i18n.changeLanguage(langCode);
            setLanguage(langCode);
            localStorage.setItem('preferred_language', langCode);
        }
    };

    useEffect(() => {
        // Sync with i18next language changes
        const handleLanguageChanged = (lng) => {
            const baseLang = lng?.split('-')[0] || 'en';
            setLanguage(baseLang);
            document.documentElement.lang = baseLang;
        };
        
        i18n.on('languageChanged', handleLanguageChanged);
        
        // Set initial HTML lang attribute
        document.documentElement.lang = language;
        
        return () => {
            i18n.off('languageChanged', handleLanguageChanged);
        };
    }, [i18n, language]);

    const value = {
        language,
        changeLanguage,
        supportedLanguages: SUPPORTED_LANGUAGES,
        currentLanguage: SUPPORTED_LANGUAGES[language] || SUPPORTED_LANGUAGES['en']
    };

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
};
