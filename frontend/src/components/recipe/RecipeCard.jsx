import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

/**
 * RecipeCard - Language-aware recipe card
 * 
 * STRICT TRANSLATION LOGIC:
 * - If translations[lang].title exists → use it
 * - Otherwise → use recipe.recipe_name (fallback)
 * - Show fallback warning ONLY when using fallback
 */
export const RecipeCard = ({ recipe }) => {
    const { t } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    
    // ======================================
    // TRANSLATION-FIRST LOGIC (User spec)
    // ======================================
    const translations = recipe.translations || {};
    const langTranslation = translations[lang] || {};
    
    // Check if we have a READY translation with actual content
    const hasTranslation = langTranslation.status === 'ready' && 
                          (langTranslation.recipe_name || langTranslation.title);
    
    // Get title: translation first, then fallback
    const title = hasTranslation
        ? (langTranslation.recipe_name || langTranslation.title)
        : (recipe.recipe_name || recipe.title_original || recipe.title_translated?.en || 'Unknown Recipe');
    
    // Get description: translation first, then fallback
    const description = hasTranslation
        ? (langTranslation.history_summary || langTranslation.characteristic_profile || langTranslation.description || '')
        : (recipe.history_summary || recipe.characteristic_profile || recipe.origin_story || '');
    
    // Show fallback banner ONLY when NOT using translation AND lang is not English
    const showFallbackBanner = !hasTranslation && lang !== 'en';
    
    // Debug log (temporary - can be removed in production)
    // console.log('[CARD]', {
    //     slug: recipe.slug,
    //     routeLang: lang,
    //     titleUsed: title,
    //     hasTranslation,
    //     translationStatus: langTranslation.status
    // });
    
    // ======================================
    // LOCALIZED UI ELEMENTS
    // ======================================
    
    // Authenticity level colors
    const levelColors = {
        1: 'bg-[#6A1F2E] text-white',
        2: 'bg-[#3F4A3C] text-white',
        3: 'bg-[#CBA55B] text-white',
        4: 'bg-gray-500 text-white',
        5: 'bg-gray-400 text-white',
    };
    
    // Localized authenticity labels
    const levelLabels = {
        1: { en: 'Official', es: 'Oficial', it: 'Ufficiale', fr: 'Officiel', de: 'Offiziell' },
        2: { en: 'Traditional', es: 'Tradicional', it: 'Tradizionale', fr: 'Traditionnel', de: 'Traditionell' },
        3: { en: 'Local', es: 'Local', it: 'Locale', fr: 'Local', de: 'Lokal' },
        4: { en: 'Recognized', es: 'Reconocido', it: 'Riconosciuto', fr: 'Reconnu', de: 'Anerkannt' },
        5: { en: 'Modern', es: 'Moderno', it: 'Moderno', fr: 'Moderne', de: 'Modern' },
    };
    
    // Localized "ingredients" label
    const ingredientLabels = {
        en: 'ingredients',
        it: 'ingredienti',
        fr: 'ingrédients',
        es: 'ingredientes',
        de: 'Zutaten'
    };
    
    // Localized fallback messages
    const fallbackMessages = {
        en: 'Shown in English',
        it: 'Mostrato in inglese',
        fr: 'Affiché en anglais',
        es: 'Mostrado en inglés',
        de: 'Auf Englisch angezeigt'
    };
    
    // ======================================
    // METADATA
    // ======================================
    const metadata = recipe.metadata || recipe;
    const country = metadata.origin_country || recipe.origin_country || recipe.country || 'Unknown';
    const region = metadata.origin_region || recipe.origin_region || recipe.region || '';
    const authenticityLevel = metadata.authenticity_level || recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;
    const slug = recipe.slug;
    const ingredientCount = recipe.content?.ingredients?.length || recipe.ingredients?.length || 0;
    
    // Get localized label
    const levelLabel = levelLabels[authenticityLevel]?.[lang] || levelLabels[authenticityLevel]?.en || levelLabels[3][lang];
    
    // Translate country name
    const countryName = t(`countries.${country}`, { defaultValue: country });
    
    // Get photo if available
    const photos = metadata.photos || recipe.photos;
    const photoUrl = photos && photos.length > 0 && photos[0].image_url 
        ? photos[0].image_url 
        : null;

    return (
        <Link to={getLocalizedPath(`/recipe/${slug}`)} data-testid={`recipe-card-${slug}`}>
            <Card className="card-elegant group cursor-pointer h-full flex flex-col">
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-[#F5F2E8]">
                    {photoUrl ? (
                        <img 
                            src={photoUrl} 
                            alt={title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <ChefHat className="h-16 w-16 text-[#CBA55B]/30" />
                        </div>
                    )}
                    <Badge className={`absolute top-3 right-3 ${levelColors[authenticityLevel] || levelColors[3]}`}>
                        <Star className="h-3 w-3 mr-1" />
                        {levelLabel}
                    </Badge>
                </div>
                
                <div className="flex-1 flex flex-col">
                    {/* Fallback warning - ONLY shown when NOT using translation */}
                    {showFallbackBanner && (
                        <div className="flex items-center gap-1 text-xs text-amber-600 mb-2">
                            <AlertCircle className="h-3 w-3" />
                            <span className="italic">{fallbackMessages[lang] || fallbackMessages.en}</span>
                        </div>
                    )}
                    
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
                    </h3>
                    
                    <p className="text-sm text-[#1E1E1E]/60 mb-3 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {countryName}{region ? ` • ${region}` : ''}
                    </p>
                    
                    {description && (
                        <p className="narrative-text text-sm line-clamp-3 flex-1">
                            {description.substring(0, 150)}{description.length > 150 ? '...' : ''}
                        </p>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center justify-between text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {ingredientLabels[lang] || ingredientLabels.en}</span>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
};

export default RecipeCard;
