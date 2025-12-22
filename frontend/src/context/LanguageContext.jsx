import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import i18n from '../i18n/i18nConfig';

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
    'es': { code: 'es', name: 'Español', flag: '🇪🇸' },
    'en': { code: 'en', name: 'English', flag: 'EN' },
    'it': { code: 'it', name: 'Italiano', flag: '🇮🇹' },
    'fr': { code: 'fr', name: 'Français', flag: '🇫🇷' },
    'de': { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
};

const LANGUAGE_CODES = ['es', 'en', 'it', 'fr', 'de'];
const DEFAULT_LANGUAGE = 'es';

// Helper to extract language from pathname
const getLanguageFromPath = (pathname) => {
    for (const code of LANGUAGE_CODES) {
        if (pathname.startsWith(`/${code}/`) || pathname === `/${code}`) {
            return code;
        }
    }
    return DEFAULT_LANGUAGE;
};

// Helper to get path without language prefix
const getPathWithoutLang = (pathname) => {
    for (const code of LANGUAGE_CODES) {
        if (pathname.startsWith(`/${code}/`)) {
            return pathname.slice(code.length + 1) || '/';
        } else if (pathname === `/${code}`) {
            return '/';
        }
    }
    return pathname;
};

// Inner provider that has access to router
const LanguageProviderInner = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    
    // Determine initial language from URL
    const initialLang = getLanguageFromPath(location.pathname);
    const [language, setLanguage] = useState(initialLang);

    // Initialize i18next with URL language on mount
    useEffect(() => {
        i18n.changeLanguage(initialLang);
        document.documentElement.lang = initialLang;
    }, []); // Run once on mount

    // Sync language with URL changes
    useEffect(() => {
        const urlLang = getLanguageFromPath(location.pathname);
        if (urlLang !== language) {
            setLanguage(urlLang);
            document.documentElement.lang = urlLang;
            // Sync with i18next
            i18n.changeLanguage(urlLang);
        }
    }, [location.pathname, language]);

    // Change language and navigate to new URL
    const changeLanguage = (langCode) => {
        if (!SUPPORTED_LANGUAGES[langCode]) return;
        
        const currentPath = getPathWithoutLang(location.pathname);
        
        // Build new path with language prefix
        let newPath;
        if (langCode === DEFAULT_LANGUAGE) {
            // Spanish: use root path (no prefix)
            newPath = currentPath === '/' ? '/' : currentPath;
        } else {
            // Other languages: add prefix
            newPath = currentPath === '/' ? `/${langCode}` : `/${langCode}${currentPath}`;
        }
        
        console.log('Changing language to:', langCode, 'New path:', newPath);
        
        setLanguage(langCode);
        document.documentElement.lang = langCode;
        localStorage.setItem('preferred_language', langCode);
        // Sync with i18next
        i18n.changeLanguage(langCode);
        
        // Navigate to new URL using window.location for reliability
        window.location.href = newPath;
    };

    // Get localized path for links
    const getLocalizedPath = useCallback((path, targetLang = language) => {
        // Clean the path first
        let cleanPath = getPathWithoutLang(path);
        
        if (targetLang === DEFAULT_LANGUAGE) {
            return cleanPath || '/';
        }
        
        if (cleanPath === '/') {
            return `/${targetLang}`;
        }
        return `/${targetLang}${cleanPath}`;
    }, [language]);

    const value = {
        language,
        changeLanguage,
        getLocalizedPath,
        supportedLanguages: SUPPORTED_LANGUAGES,
        currentLanguage: SUPPORTED_LANGUAGES[language] || SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE],
        defaultLanguage: DEFAULT_LANGUAGE,
        isDefaultLanguage: language === DEFAULT_LANGUAGE
    };

    return (
        <LanguageContext.Provider value={value}>
            {children}
        </LanguageContext.Provider>
    );
};

// Outer provider for use outside Router
export const LanguageProvider = ({ children }) => {
    return children;
};

// This is the actual provider to use inside BrowserRouter
export const LanguageRouterProvider = ({ children }) => {
    return (
        <LanguageProviderInner>
            {children}
        </LanguageProviderInner>
    );
};
