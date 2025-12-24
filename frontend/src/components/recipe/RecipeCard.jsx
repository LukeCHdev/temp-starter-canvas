import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

/**
 * RecipeCard - Language-aware recipe card with STRICT fallback indicators
 * 
 * TRANSLATION LOGIC:
 * - If translations[lang].status === 'ready' → use translated content (no marker)
 * - Otherwise → use English fallback with VISIBLE markers:
 *   1. (EN) badge on image (top-left)
 *   2. (EN) next to title
 *   3. Localized "Translation pending" text at bottom
 * 
 * NO SILENT FALLBACK - users always know when viewing English content
 */
export const RecipeCard = ({ recipe }) => {
    const { t } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    
    // ======================================
    // TRANSLATION-FIRST LOGIC
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
    
    // STRICT: Show fallback indicators when NOT using translation AND lang is not English
    const showFallbackIndicator = !hasTranslation && lang !== 'en';
    
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
    
    // Localized "Translation pending" messages
    const pendingMessages = {
        en: 'Translation pending',
        it: 'Traduzione in corso',
        fr: 'Traduction en attente',
        es: 'Traducción pendiente',
        de: 'Übersetzung ausstehend'
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
                {/* Image Section with Badges */}
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-[#F5F2E8]">
                    {photoUrl ? (
                        <img 
                            src={photoUrl} 
                            alt={title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <ChefHat className="h-16 w-16 text-[#CBA55B]/30" />
                        </div>
                    )}
                    
                    {/* Authenticity Badge (top-right) */}
                    <Badge className={`absolute top-3 right-3 ${levelColors[authenticityLevel] || levelColors[3]}`}>
                        <Star className="h-3 w-3 mr-1" />
                        {levelLabel}
                    </Badge>
                    
                    {/* FALLBACK INDICATOR: (EN) Badge on image (top-left) */}
                    {showFallbackIndicator && (
                        <Badge variant="outline" className="absolute top-3 left-3 bg-amber-50 border-amber-300 text-amber-700 text-xs font-medium">
                            (EN)
                        </Badge>
                    )}
                </div>
                
                {/* Content Section */}
                <div className="flex-1 flex flex-col">
                    {/* Title with inline (EN) marker */}
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
                        {showFallbackIndicator && (
                            <span className="ml-2 text-xs font-normal text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                                (EN)
                            </span>
                        )}
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
                    
                    {/* Footer with ingredients and translation status */}
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center justify-between text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {ingredientLabels[lang] || ingredientLabels.en}</span>
                        )}
                        {/* FALLBACK INDICATOR: "Translation pending" text */}
                        {showFallbackIndicator && (
                            <span className="text-xs text-amber-600">
                                {pendingMessages[lang] || pendingMessages.en}
                            </span>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
};

export default RecipeCard;
