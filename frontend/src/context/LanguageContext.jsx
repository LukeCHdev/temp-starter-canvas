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

// Helper to extract language from URL path
const getLanguageFromPath = (pathname) => {
    const segments = pathname.split('/').filter(Boolean);
    if (segments.length > 0 && SUPPORTED_LANGUAGES[segments[0]]) {
        return segments[0];
    }
    return 'es'; // Default to Spanish
};

// Helper to update path with new language
const updatePathLanguage = (pathname, newLang) => {
    const segments = pathname.split('/').filter(Boolean);
    const currentLang = SUPPORTED_LANGUAGES[segments[0]] ? segments[0] : null;
    
    if (currentLang) {
        segments[0] = newLang;
    } else if (newLang !== 'es') {
        segments.unshift(newLang);
    }
    
    // For Spanish (default), don't add prefix
    if (newLang === 'es' && segments[0] === 'es') {
        segments.shift();
    }
    
    return '/' + segments.join('/') || '/';
};

// Inner provider that uses router hooks
const LanguageProviderInner = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    
    // Get initial language from URL
    const initialLang = useMemo(() => getLanguageFromPath(location.pathname), []);
    const [language, setLanguage] = useState(initialLang);
    
    // Initialize i18n on mount
    useEffect(() => {
        i18n.changeLanguage(initialLang);
        document.documentElement.lang = initialLang;
    }, [initialLang]);

    // Sync language with URL changes (only when URL actually changes)
    useEffect(() => {
        const urlLang = getLanguageFromPath(location.pathname);
        if (urlLang !== language) {
            setLanguage(urlLang);
            i18n.changeLanguage(urlLang);
            document.documentElement.lang = urlLang;
        }
    }, [location.pathname]); // Remove 'language' from deps to prevent loops

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
        
        // Navigate to new URL
        const newPath = updatePathLanguage(location.pathname, langCode);
        navigate(newPath, { replace: true });
    }, [language, location.pathname, navigate]);

    // Memoized context value to prevent unnecessary re-renders
    const contextValue = useMemo(() => ({
        language,
        changeLanguage,
        supportedLanguages: SUPPORTED_LANGUAGES,
        isDefaultLanguage: language === 'es',
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
