import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star, Loader2, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

/**
 * TranslatedRecipeCard - LANGUAGE-COHERENT Recipe Card Component
 * 
 * STRICT LANGUAGE RULES:
 * 1. status='ready' + is_translated=true → Show translated content in target language
 * 2. status='ready' + is_translated=false → Show canonical English content (no marker needed if en)
 * 3. status='fallback' → Show English content with visible (EN) marker
 * 4. NEVER silently show content in IT/ES/PT etc. without explicit marker
 * 
 * Fallback indicators:
 * - (EN) = English fallback when translation not available
 * - Shows origin language only if explicitly requested
 */
export const TranslatedRecipeCard = ({ recipe }) => {
    const { t } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    
    // Destructure with defaults
    const { 
        status = 'unknown', 
        content = {}, 
        metadata = {}, 
        slug = '',
        is_translated = false,
        fallback_lang = null,
        lang: contentLang = 'en'
    } = recipe || {};
    
    // Current UI language from context (derived from URL)
    const currentLang = language || 'en';
    
    // Authenticity level styling
    const levelColors = {
        1: 'bg-[#6A1F2E] text-white',
        2: 'bg-[#3F4A3C] text-white',
        3: 'bg-[#CBA55B] text-white',
        4: 'bg-gray-500 text-white',
        5: 'bg-gray-400 text-white',
    };
    
    const levelLabels = {
        1: { en: 'Official', es: 'Oficial', it: 'Ufficiale', fr: 'Officiel', de: 'Offiziell' },
        2: { en: 'Traditional', es: 'Tradicional', it: 'Tradizionale', fr: 'Traditionnel', de: 'Traditionell' },
        3: { en: 'Local', es: 'Local', it: 'Locale', fr: 'Local', de: 'Lokal' },
        4: { en: 'Recognized', es: 'Reconocido', it: 'Riconosciuto', fr: 'Reconnu', de: 'Anerkannt' },
        5: { en: 'Modern', es: 'Moderno', it: 'Moderno', fr: 'Moderne', de: 'Modern' },
    };
    
    const authenticityLevel = metadata?.authenticity_level || 3;
    const levelLabel = levelLabels[authenticityLevel]?.[currentLang] || levelLabels[authenticityLevel]?.en || 'Traditional';
    
    // Get photo URL
    const photoUrl = metadata?.photos?.[0]?.image_url || null;
    
    /**
     * Determine if we need to show a language fallback marker
     * Rules:
     * - If status='fallback' and currentLang !== 'en' → show (EN)
     * - If content is ready and matches currentLang → no marker needed
     * - If currentLang === 'en' and content is English → no marker needed
     */
    const showFallbackMarker = status === 'fallback' && currentLang !== 'en';
    const fallbackMarkerText = fallback_lang ? `(${fallback_lang.toUpperCase()})` : '(EN)';
    
    // Extract content fields safely
    const title = content?.recipe_name || 'Unknown Recipe';
    const description = content?.history_summary || content?.characteristic_profile || '';
    const ingredientCount = content?.ingredients?.length || 0;
    
    // Localized country/region names
    const countryName = t(`countries.${metadata?.origin_country}`, { defaultValue: metadata?.origin_country || 'Unknown' });
    const regionName = metadata?.origin_region || '';
    
    // Render content based on status
    const renderContent = () => {
        // CASE 1 & 2: Ready or Fallback with content - render immediately
        if ((status === 'ready' || status === 'fallback') && content && title) {
            return (
                <>
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
                        {showFallbackMarker && (
                            <span className="ml-2 text-xs font-normal text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                                {fallbackMarkerText}
                            </span>
                        )}
                    </h3>
                    
                    <p className="text-sm text-[#1E1E1E]/60 mb-3 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {countryName}{regionName && ` • ${regionName}`}
                    </p>
                    
                    {description && (
                        <p className="narrative-text text-sm line-clamp-3 flex-1">
                            {description.substring(0, 150)}{description.length > 150 ? '...' : ''}
                        </p>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center justify-between text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {t('recipe.ingredients', { defaultValue: 'ingredients' })}</span>
                        )}
                        {status === 'fallback' && (
                            <span className="text-xs text-amber-600">
                                {t('recipe.translationPending', { defaultValue: 'Translation pending' })}
                            </span>
                        )}
                    </div>
                </>
            );
        }
        
        // CASE 3: Pending translation
        if (status === 'pending') {
            return (
                <div className="flex flex-col items-center justify-center h-full py-8">
                    <Loader2 className="h-8 w-8 text-[#6A1F2E] animate-spin mb-3" />
                    <p className="text-sm text-[#1E1E1E]/60 text-center">
                        {t('recipe.translating', { defaultValue: 'Translating...' })}
                    </p>
                    <p className="text-xs text-[#1E1E1E]/40 mt-2">
                        {metadata?.origin_country || ''}
                    </p>
                </div>
            );
        }
        
        // CASE 4: Failed translation
        if (status === 'failed') {
            return (
                <div className="flex flex-col items-center justify-center h-full py-8">
                    <AlertCircle className="h-8 w-8 text-amber-500/50 mb-3" />
                    <p className="text-sm text-[#1E1E1E]/60 text-center">
                        {t('recipe.translationUnavailable', { defaultValue: 'Translation unavailable' })}
                    </p>
                    <p className="text-xs text-[#1E1E1E]/40 mt-2">
                        {metadata?.origin_country || ''}
                    </p>
                </div>
            );
        }
        
        // CASE 5: Unknown status - generic placeholder
        return (
            <div className="flex flex-col items-center justify-center h-full py-8">
                <ChefHat className="h-8 w-8 text-[#CBA55B]/50 mb-3" />
                <p className="text-sm text-[#1E1E1E]/60">
                    {t('recipe.loadingRecipe', { defaultValue: 'Loading recipe...' })}
                </p>
            </div>
        );
    };
    
    return (
        <Link to={getLocalizedPath(`/recipe/${slug}`)} data-testid={`recipe-card-${slug}`}>
            <Card className="card-elegant group cursor-pointer h-full flex flex-col">
                {/* Image Section */}
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
                    
                    {/* Authenticity Badge */}
                    <Badge className={`absolute top-3 right-3 ${levelColors[authenticityLevel] || levelColors[3]}`}>
                        <Star className="h-3 w-3 mr-1" />
                        {levelLabel}
                    </Badge>
                    
                    {/* Fallback Language Indicator (top-left) */}
                    {showFallbackMarker && (
                        <Badge variant="outline" className="absolute top-3 left-3 bg-amber-50 border-amber-300 text-amber-700 text-xs">
                            {fallbackMarkerText}
                        </Badge>
                    )}
                </div>
                
                {/* Content Section */}
                <div className="flex-1 flex flex-col">
                    {renderContent()}
                </div>
            </Card>
        </Link>
    );
};

export default TranslatedRecipeCard;
