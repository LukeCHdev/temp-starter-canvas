import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

/**
 * TranslatedRecipeCard - LANGUAGE-COHERENT Recipe Card Component (SEO-READY)
 * 
 * STRICT LANGUAGE RULES:
 * - Uses translated content when available
 * - Falls back to English content for display
 * - NO fallback indicators shown (clean UI for production/SEO)
 * 
 * Note: Strict gating (hiding untranslated recipes) is handled at the API/data layer
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
    
    // Get photo URL — check photos array first, then top-level image_url (Unsplash)
    const photoUrl = (metadata?.photos && metadata.photos.length > 0 && metadata.photos[0]?.image_url)
        ? metadata.photos[0].image_url
        : (metadata?.image_url || null);
    
    // Extract content fields safely
    const title = content?.recipe_name || 'Unknown Recipe';
    const description = content?.history_summary || content?.characteristic_profile || '';
    const ingredientCount = content?.ingredients?.length || 0;
    
    // Localized country/region names
    const countryName = t(`countries.${metadata?.origin_country}`, { defaultValue: metadata?.origin_country || 'Unknown' });
    const regionName = metadata?.origin_region || '';
    
    // Render content - always show content without fallback indicators
    const renderContent = () => {
        // Show content if available (ready or fallback - no indicators)
        if ((status === 'ready' || status === 'fallback') && content && title) {
            return (
                <>
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
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
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {t('recipe.ingredients', { defaultValue: 'ingredients' })}</span>
                        )}
                    </div>
                </>
            );
        }
        
        // For pending/failed/unknown - show minimal placeholder
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
