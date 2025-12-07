import React, { createContext, useContext, useState, useEffect } from 'react';

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
    // Detect browser language or use stored preference
    const detectLanguage = () => {
        const stored = localStorage.getItem('preferred_language');
        if (stored && SUPPORTED_LANGUAGES[stored]) {
            return stored;
        }
        
        // Detect from browser
        const browserLang = navigator.language.split('-')[0];
        return SUPPORTED_LANGUAGES[browserLang] ? browserLang : 'en';
    };

    const [language, setLanguage] = useState(detectLanguage());

    const changeLanguage = (langCode) => {
        if (SUPPORTED_LANGUAGES[langCode]) {
            setLanguage(langCode);
            localStorage.setItem('preferred_language', langCode);
        }
    };

    useEffect(() => {
        // Set HTML lang attribute
        document.documentElement.lang = language;
    }, [language]);

    const value = {
        language,
        changeLanguage,
        supportedLanguages: SUPPORTED_LANGUAGES,
        currentLanguage: SUPPORTED_LANGUAGES[language]
    };

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
};
