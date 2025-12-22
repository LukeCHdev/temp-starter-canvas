import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import i18n from '../i18n/i18nConfig';

const LanguageContext = createContext(null);

// Supported languages configuration
export const SUPPORTED_LANGUAGES = {
    'en': { code: 'en', name: 'English', flag: 'EN' },
    'es': { code: 'es', name: 'Español', flag: 'ES' },
    'it': { code: 'it', name: 'Italiano', flag: 'IT' },
    'fr': { code: 'fr', name: 'Français', flag: 'FR' },
    'de': { code: 'de', name: 'Deutsch', flag: 'DE' },
};

// Default fallback language (only used if nothing else available)
const DEFAULT_LANGUAGE = 'en';

// Helper to extract language from URL path
const getLanguageFromPath = (pathname) => {
    const segments = pathname.split('/').filter(Boolean);
    if (segments.length > 0 && SUPPORTED_LANGUAGES[segments[0]]) {
        return segments[0];
    }
    return null; // Return null if no language in URL
};

// Get language with fallback logic (URL -> localStorage -> default)
const getInitialLanguage = (pathname) => {
    // 1. First try URL
    const urlLang = getLanguageFromPath(pathname);
    if (urlLang) return urlLang;
    
    // 2. Then try localStorage
    const storedLang = localStorage.getItem('preferred_language');
    if (storedLang && SUPPORTED_LANGUAGES[storedLang]) return storedLang;
    
    // 3. Finally fallback to English (NOT Spanish)
    return DEFAULT_LANGUAGE;
};

// Helper to get language-prefixed path
export const getLocalizedPath = (path, language) => {
    // Remove any existing language prefix
    const cleanPath = path.replace(/^\/(en|es|it|fr|de)(\/|$)/, '/');
    
    // Always add language prefix for consistency
    if (cleanPath === '/' || cleanPath === '') {
        return `/${language}`;
    }
    return `/${language}${cleanPath.startsWith('/') ? '' : '/'}${cleanPath}`;
};

// Inner provider that uses router hooks
const LanguageProviderInner = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    
    // Get initial language with proper fallback
    const initialLang = useMemo(() => getInitialLanguage(location.pathname), []);
    const [language, setLanguage] = useState(initialLang);
    
    // Initialize i18n and persist on mount
    useEffect(() => {
        i18n.changeLanguage(initialLang);
        document.documentElement.lang = initialLang;
        localStorage.setItem('preferred_language', initialLang);
        
        // If URL doesn't have language prefix, add it
        const urlLang = getLanguageFromPath(location.pathname);
        if (!urlLang) {
            const newPath = getLocalizedPath(location.pathname, initialLang);
            navigate(newPath, { replace: true });
        }
    }, [initialLang, location.pathname, navigate]);

    // Sync language with URL changes - this is the SINGLE SOURCE OF TRUTH
    useEffect(() => {
        const urlLang = getLanguageFromPath(location.pathname);
        if (urlLang) {
            // Always sync i18n with URL language
            if (i18n.language !== urlLang) {
                i18n.changeLanguage(urlLang);
            }
            // Update state if different
            if (urlLang !== language) {
                setLanguage(urlLang);
                document.documentElement.lang = urlLang;
                localStorage.setItem('preferred_language', urlLang);
            }
        }
    }, [location.pathname, language]);

    // Stable change language function
    const changeLanguage = useCallback((langCode) => {
        if (!SUPPORTED_LANGUAGES[langCode] || langCode === language) {
            return;
        }
        
        // Update state
        setLanguage(langCode);
        document.documentElement.lang = langCode;
        localStorage.setItem('preferred_language', langCode);
        
        // Sync with i18next
        i18n.changeLanguage(langCode);
        
        // Navigate to new URL with language prefix
        const newPath = getLocalizedPath(location.pathname, langCode);
        navigate(newPath, { replace: true });
    }, [language, location.pathname, navigate]);

    // Memoized context value to prevent unnecessary re-renders
    const contextValue = useMemo(() => ({
        language,
        changeLanguage,
        supportedLanguages: SUPPORTED_LANGUAGES,
        isDefaultLanguage: language === DEFAULT_LANGUAGE,
        getLocalizedPath: (path) => getLocalizedPath(path, language),
    }), [language, changeLanguage]);

    return (
        <LanguageContext.Provider value={contextValue}>
            {children}
        </LanguageContext.Provider>
    );
};

// Main provider wrapper
export const LanguageProvider = ({ children }) => {
    return (
        <LanguageProviderInner>
            {children}
        </LanguageProviderInner>
    );
};

// Hook to use language context
export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
};

export default LanguageContext;
