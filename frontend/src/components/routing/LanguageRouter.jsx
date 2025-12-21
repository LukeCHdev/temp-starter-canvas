import React, { useEffect } from 'react';
import { useParams, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';

// Supported language codes for URL prefixes
const LANGUAGE_CODES = ['es', 'en', 'it', 'fr', 'de'];
const DEFAULT_LANGUAGE = 'es';

/**
 * LanguageRouter - Handles language prefix in URLs
 * 
 * URL Structure:
 * - / → Spanish (default)
 * - /es/* → Spanish (explicit)
 * - /en/* → English
 * - /it/* → Italian
 * - /fr/* → French
 * - /de/* → German
 */
export const LanguageRouter = ({ children }) => {
    const { lang } = useParams();
    const { changeLanguage, language } = useLanguage();
    const location = useLocation();

    useEffect(() => {
        // Determine language from URL
        if (lang && LANGUAGE_CODES.includes(lang)) {
            // URL has explicit language prefix
            if (lang !== language) {
                changeLanguage(lang);
            }
        } else if (!lang) {
            // No prefix = default to Spanish
            if (language !== DEFAULT_LANGUAGE) {
                changeLanguage(DEFAULT_LANGUAGE);
            }
        }
    }, [lang, changeLanguage, language]);

    return children || <Outlet />;
};

/**
 * Hook to get language-aware paths
 */
export const useLanguagePath = () => {
    const { language } = useLanguage();
    const location = useLocation();
    const navigate = useNavigate();

    // Generate path with language prefix
    const getLocalizedPath = (path, targetLang = language) => {
        // Remove any existing language prefix
        let cleanPath = path;
        for (const code of LANGUAGE_CODES) {
            if (cleanPath.startsWith(`/${code}/`)) {
                cleanPath = cleanPath.slice(code.length + 1);
                break;
            } else if (cleanPath === `/${code}`) {
                cleanPath = '/';
                break;
            }
        }

        // Spanish (default) can be at root or /es
        if (targetLang === DEFAULT_LANGUAGE) {
            // For Spanish, prefer root path (no prefix)
            return cleanPath || '/';
        }

        // Other languages get prefix
        if (cleanPath === '/') {
            return `/${targetLang}`;
        }
        return `/${targetLang}${cleanPath}`;
    };

    // Navigate with language prefix
    const navigateWithLang = (path, options) => {
        const localizedPath = getLocalizedPath(path);
        navigate(localizedPath, options);
    };

    // Get current path without language prefix
    const getCurrentPathWithoutLang = () => {
        let path = location.pathname;
        for (const code of LANGUAGE_CODES) {
            if (path.startsWith(`/${code}/`)) {
                return path.slice(code.length + 1) || '/';
            } else if (path === `/${code}`) {
                return '/';
            }
        }
        return path;
    };

    return {
        getLocalizedPath,
        navigateWithLang,
        getCurrentPathWithoutLang,
        currentLanguage: language,
        defaultLanguage: DEFAULT_LANGUAGE,
        supportedLanguages: LANGUAGE_CODES
    };
};

/**
 * Helper to extract language from pathname
 */
export const getLanguageFromPath = (pathname) => {
    for (const code of LANGUAGE_CODES) {
        if (pathname.startsWith(`/${code}/`) || pathname === `/${code}`) {
            return code;
        }
    }
    return DEFAULT_LANGUAGE; // Default to Spanish
};

export { LANGUAGE_CODES, DEFAULT_LANGUAGE };
