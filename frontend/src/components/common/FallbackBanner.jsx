import React from 'react';
import { AlertCircle, Globe } from 'lucide-react';
import { useTranslation } from 'react-i18next';

/**
 * FallbackBanner - Displays a subtle notification when content is shown in a different language
 * 
 * Props:
 * - contentLang: The language the content is actually displayed in
 * - requestedLang: The language the user requested (from URL)
 * - onRequestTranslation: Optional callback to request translation
 */
export const FallbackBanner = ({ contentLang, requestedLang, onRequestTranslation }) => {
    const { t } = useTranslation();
    
    // Language names for display
    const languageNames = {
        en: { en: 'English', it: 'Inglese', fr: 'Anglais', es: 'Inglés', de: 'Englisch' },
        it: { en: 'Italian', it: 'Italiano', fr: 'Italien', es: 'Italiano', de: 'Italienisch' },
        fr: { en: 'French', it: 'Francese', fr: 'Français', es: 'Francés', de: 'Französisch' },
        es: { en: 'Spanish', it: 'Spagnolo', fr: 'Espagnol', es: 'Español', de: 'Spanisch' },
        de: { en: 'German', it: 'Tedesco', fr: 'Allemand', es: 'Alemán', de: 'Deutsch' },
    };
    
    // Get display name of content language in requested language
    const contentLangName = languageNames[contentLang]?.[requestedLang] || languageNames[contentLang]?.en || contentLang.toUpperCase();
    
    // Messages in all supported languages
    const messages = {
        en: `This recipe is currently shown in ${contentLangName}. Translation coming soon.`,
        it: `Questa ricetta è attualmente mostrata in ${contentLangName}. Traduzione in arrivo.`,
        fr: `Cette recette est actuellement affichée en ${contentLangName}. Traduction à venir.`,
        es: `Esta receta se muestra actualmente en ${contentLangName}. Traducción próximamente.`,
        de: `Dieses Rezept wird derzeit auf ${contentLangName} angezeigt. Übersetzung folgt.`,
    };
    
    const message = messages[requestedLang] || messages.en;
    
    // Don't render if languages match
    if (contentLang === requestedLang) {
        return null;
    }
    
    return (
        <div 
            className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6 rounded-r-lg"
            role="alert"
            data-testid="fallback-banner"
        >
            <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                    <Globe className="h-5 w-5 text-amber-600" />
                </div>
                <div className="flex-1">
                    <p className="text-sm text-amber-800">
                        {message}
                    </p>
                </div>
            </div>
        </div>
    );
};

/**
 * TranslationPendingBanner - Shows when translation is in progress
 */
export const TranslationPendingBanner = ({ requestedLang }) => {
    const messages = {
        en: 'Translation in progress... Please check back soon.',
        it: 'Traduzione in corso... Torna a trovarci presto.',
        fr: 'Traduction en cours... Revenez bientôt.',
        es: 'Traducción en progreso... Vuelve pronto.',
        de: 'Übersetzung läuft... Bitte schauen Sie bald wieder vorbei.',
    };
    
    return (
        <div 
            className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6 rounded-r-lg"
            role="status"
            data-testid="translation-pending-banner"
        >
            <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                    <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
                <p className="text-sm text-blue-800">
                    {messages[requestedLang] || messages.en}
                </p>
            </div>
        </div>
    );
};

/**
 * TranslationFailedBanner - Shows when translation failed
 */
export const TranslationFailedBanner = ({ contentLang, requestedLang }) => {
    const languageNames = {
        en: { en: 'English', it: 'Inglese', fr: 'Anglais', es: 'Inglés', de: 'Englisch' },
        it: { en: 'Italian', it: 'Italiano', fr: 'Italien', es: 'Italiano', de: 'Italienisch' },
        fr: { en: 'French', it: 'Francese', fr: 'Français', es: 'Francés', de: 'Französisch' },
        es: { en: 'Spanish', it: 'Spagnolo', fr: 'Espagnol', es: 'Español', de: 'Spanisch' },
        de: { en: 'German', it: 'Tedesco', fr: 'Allemand', es: 'Alemán', de: 'Deutsch' },
    };
    
    const contentLangName = languageNames[contentLang]?.[requestedLang] || contentLang.toUpperCase();
    
    const messages = {
        en: `Translation unavailable. Showing content in ${contentLangName}.`,
        it: `Traduzione non disponibile. Contenuto mostrato in ${contentLangName}.`,
        fr: `Traduction non disponible. Contenu affiché en ${contentLangName}.`,
        es: `Traducción no disponible. Mostrando contenido en ${contentLangName}.`,
        de: `Übersetzung nicht verfügbar. Inhalt wird auf ${contentLangName} angezeigt.`,
    };
    
    return (
        <div 
            className="bg-gray-50 border-l-4 border-gray-400 p-4 mb-6 rounded-r-lg"
            role="alert"
            data-testid="translation-failed-banner"
        >
            <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-gray-600 flex-shrink-0" />
                <p className="text-sm text-gray-700">
                    {messages[requestedLang] || messages.en}
                </p>
            </div>
        </div>
    );
};

export default FallbackBanner;
