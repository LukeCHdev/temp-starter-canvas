/**
 * Regional Variants Translation System
 * 
 * Uses base translations (es.json, fr.json) with regional overrides (es-MX.json, fr-CA.json)
 * Fallback: regional -> base language -> English
 */

// Supported regional variants
export const REGIONAL_VARIANTS = {
    'es-MX': { base: 'es', name: 'Español (México)', flag: '🇲🇽' },
    'es-AR': { base: 'es', name: 'Español (Argentina)', flag: '🇦🇷' },
    'es-CO': { base: 'es', name: 'Español (Colombia)', flag: '🇨🇴' },
    'fr-CA': { base: 'fr', name: 'Français (Canada)', flag: '🇨🇦' },
    'fr-BE': { base: 'fr', name: 'Français (Belgique)', flag: '🇧🇪' },
    'pt-BR': { base: 'pt', name: 'Português (Brasil)', flag: '🇧🇷' },
    'en-US': { base: 'en', name: 'English (US)', flag: '🇺🇸' },
    'en-GB': { base: 'en', name: 'English (UK)', flag: '🇬🇧' },
    'de-AT': { base: 'de', name: 'Deutsch (Österreich)', flag: '🇦🇹' },
    'de-CH': { base: 'de', name: 'Deutsch (Schweiz)', flag: '🇨🇭' },
};

// Regional overrides for Spanish (Mexico)
export const esMX = {
    // Cooking terms that differ in Mexico
    cooking: {
        pan: 'sartén',           // In Spain: sartén, in Mexico: sartén (same)
        stove: 'estufa',         // In Spain: cocina, in Mexico: estufa
        fridge: 'refrigerador',  // In Spain: nevera, in Mexico: refrigerador
        beans: 'frijoles',       // In Spain: judías/alubias, in Mexico: frijoles
        corn: 'elote',           // In Spain: maíz, in Mexico: elote (fresh)
        avocado: 'aguacate',     // In Spain: aguacate (same)
        pepper: 'chile',         // In Spain: pimiento, in Mexico: chile
        turkey: 'guajolote',     // In Spain: pavo, in Mexico: guajolote
        banana: 'plátano',       // Same
        peanut: 'cacahuate',     // In Spain: cacahuete, in Mexico: cacahuate
        potato: 'papa',          // In Spain: patata, in Mexico: papa
        juice: 'jugo',           // In Spain: zumo, in Mexico: jugo
    },
    // UI text overrides
    common: {
        search: 'Buscar',
        cancel: 'Cancelar',
        // Add more as needed
    }
};

// Regional overrides for French (Canada)
export const frCA = {
    // Cooking terms that differ in Quebec
    cooking: {
        breakfast: 'déjeuner',      // In France: petit-déjeuner, in Quebec: déjeuner
        lunch: 'dîner',             // In France: déjeuner, in Quebec: dîner
        dinner: 'souper',           // In France: dîner, in Quebec: souper
        blueberry: 'bleuet',        // In France: myrtille, in Quebec: bleuet
        corn: 'blé d\'Inde',        // In France: maïs, in Quebec: blé d'Inde
        cranberry: 'canneberge',    // Same but more common in Quebec
        maple_syrup: 'sirop d\'érable',  // Same but iconic in Quebec
    },
    // UI text overrides
    common: {
        email: 'courriel',          // In France: e-mail, in Quebec: courriel
        weekend: 'fin de semaine',  // In France: week-end, in Quebec: fin de semaine
    }
};

// Regional overrides for Portuguese (Brazil)
export const ptBR = {
    cooking: {
        juice: 'suco',              // In Portugal: sumo, in Brazil: suco
        bus: 'ônibus',              // In Portugal: autocarro, in Brazil: ônibus
        train: 'trem',              // In Portugal: comboio, in Brazil: trem
        bathroom: 'banheiro',       // In Portugal: casa de banho, in Brazil: banheiro
        breakfast: 'café da manhã', // In Portugal: pequeno-almoço, in Brazil: café da manhã
    }
};

// Regional overrides for English (UK)
export const enGB = {
    cooking: {
        eggplant: 'aubergine',
        zucchini: 'courgette',
        cilantro: 'coriander',
        arugula: 'rocket',
        shrimp: 'prawns',
        cookies: 'biscuits',
        chips: 'crisps',
        fries: 'chips',
        broil: 'grill',
        ground_beef: 'minced beef',
    },
    // Measurements
    measurements: {
        cup: 'cup (240ml)',
        tablespoon: 'tablespoon (15ml)',
        teaspoon: 'teaspoon (5ml)',
    }
};

/**
 * Deep merge two objects, with override taking precedence
 */
export const deepMerge = (base, override) => {
    if (!override) return base;
    if (!base) return override;
    
    const result = { ...base };
    
    for (const key of Object.keys(override)) {
        if (override[key] && typeof override[key] === 'object' && !Array.isArray(override[key])) {
            result[key] = deepMerge(base[key], override[key]);
        } else {
            result[key] = override[key];
        }
    }
    
    return result;
};

/**
 * Get translations for a locale with fallback chain
 * @param {string} locale - Full locale code (e.g., 'es-MX', 'fr', 'en')
 * @param {object} translations - Base translations object
 * @returns {object} Merged translations
 */
export const getTranslationsForLocale = (locale, translations) => {
    // Check if it's a regional variant
    const variant = REGIONAL_VARIANTS[locale];
    
    if (variant) {
        // Get base language translations
        const baseTranslations = translations[variant.base] || translations['en'];
        
        // Get regional overrides
        let overrides = {};
        switch (locale) {
            case 'es-MX':
            case 'es-AR':
            case 'es-CO':
                overrides = esMX;
                break;
            case 'fr-CA':
            case 'fr-BE':
                overrides = frCA;
                break;
            case 'pt-BR':
                overrides = ptBR;
                break;
            case 'en-GB':
                overrides = enGB;
                break;
            default:
                overrides = {};
        }
        
        // Merge base with overrides
        return deepMerge(baseTranslations, overrides);
    }
    
    // Not a regional variant, return base translations
    return translations[locale] || translations['en'];
};

/**
 * Parse locale and extract base language
 * @param {string} locale - Locale code (e.g., 'es-MX', 'fr', 'en-US')
 * @returns {object} { language, region, isRegional }
 */
export const parseLocale = (locale) => {
    if (!locale) return { language: 'en', region: null, isRegional: false };
    
    const parts = locale.split('-');
    const language = parts[0].toLowerCase();
    const region = parts[1]?.toUpperCase() || null;
    
    return {
        language,
        region,
        isRegional: region !== null,
        fullLocale: region ? `${language}-${region}` : language
    };
};

/**
 * Get the best matching locale from available options
 * @param {string} requested - Requested locale
 * @param {string[]} available - Available locales
 * @returns {string} Best matching locale
 */
export const getBestMatchingLocale = (requested, available) => {
    // Exact match
    if (available.includes(requested)) {
        return requested;
    }
    
    // Try base language
    const { language } = parseLocale(requested);
    if (available.includes(language)) {
        return language;
    }
    
    // Fallback to English
    return 'en';
};

export default {
    REGIONAL_VARIANTS,
    esMX,
    frCA,
    ptBR,
    enGB,
    deepMerge,
    getTranslationsForLocale,
    parseLocale,
    getBestMatchingLocale
};
