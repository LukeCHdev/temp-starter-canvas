import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';

/**
 * RecipeCard - Language-aware recipe card with STRICT LANGUAGE GATING
 * 
 * TRANSLATION LOGIC (SEO-READY):
 * - Uses translated content when available (status: 'ready')
 * - Falls back to English content for display
 * - NO fallback indicators shown (clean UI for production/SEO)
 * 
 * Note: Strict gating (hiding untranslated recipes) is handled at the API/data layer
 */
export const RecipeCard = ({ recipe, variant = 'default' }) => {
    const { t: i18nT } = useTranslation();
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
    
    // Get title: translation first, then fallback to English
    const title = hasTranslation
        ? (langTranslation.recipe_name || langTranslation.title)
        : (recipe.recipe_name || recipe.title_original || recipe.title_translated?.en || 'Unknown Recipe');
    
    // Get description: translation first, then fallback to English
    const description = hasTranslation
        ? (langTranslation.history_summary || langTranslation.characteristic_profile || langTranslation.description || '')
        : (recipe.history_summary || recipe.characteristic_profile || recipe.origin_story || '');
    
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
    
    // ======================================
    // METADATA
    // ======================================
    const metadata = recipe.metadata || recipe;
    const country = metadata.origin_country || recipe.origin_country || recipe.country || 'Unknown';
    const region = metadata.origin_region || recipe.origin_region || recipe.region || '';
    const authenticityLevel = metadata.authenticity_level || recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;
    const slug = recipe.slug;
    const ingredientCount = recipe.content?.ingredients?.length || recipe.ingredients?.length || 0;
    
    // Get localized label - use translation function
    const levelLabel = t(`badges.${authenticityLevel === 1 ? 'officiallyRecognized' : authenticityLevel === 2 ? 'traditionVerified' : 'traditional'}`, lang);
    
    // Translate country name
    const countryName = i18nT(`countries.${country}`, { defaultValue: country });
    
    // Get photo if available — check photos array first, then top-level image_url (Unsplash)
    const photos = metadata.photos || recipe.photos;
    const photoUrl = (photos && photos.length > 0 && photos[0].image_url)
        ? photos[0].image_url 
        : (recipe.image_url || null);

    // Editorial variant - cleaner, more refined design
    if (variant === 'editorial') {
        return (
            <Link to={getLocalizedPath(`/recipe/${slug}`)} data-testid={`recipe-card-${slug}`}>
                <article className="group h-full bg-white border border-[#E8E4DC] hover:border-[#6A1F2E] transition-colors">
                    {/* Image */}
                    <div className="relative overflow-hidden h-56 bg-[#F5F2EC]">
                        {photoUrl ? (
                            <img 
                                src={photoUrl} 
                                alt={title}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                loading="lazy"
                            />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-[#BFBFBF] text-4xl font-light" style={{ fontFamily: 'Cormorant Garamond, serif' }}>SCL</span>
                            </div>
                        )}
                    </div>
                    
                    {/* Content */}
                    <div className="p-6">
                        {/* Authenticity Badge */}
                        <span className="inline-block text-xs uppercase tracking-widest text-[#6A1F2E] mb-3">
                            {levelLabel}
                        </span>
                        
                        {/* Origin */}
                        <p className="text-xs text-[#7C7C7C] mb-2 tracking-wide">
                            {countryName}{region ? ` · ${region}` : ''}
                        </p>
                        
                        {/* Title */}
                        <h3 className="text-lg font-light text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors line-clamp-2 mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {title}
                        </h3>
                        
                        {/* Rating/Authenticity Score */}
                        {recipe.average_rating && (
                            <div className="flex items-center gap-2 text-xs text-[#7C7C7C]">
                                <Star className="h-3 w-3 fill-[#CBA55B] text-[#CBA55B]" />
                                <span>{recipe.average_rating.toFixed(1)} {t('explore.authenticityScore', lang)}</span>
                            </div>
                        )}
                    </div>
                </article>
            </Link>
        );
    }

    // Default variant

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
                </div>
                
                {/* Content Section */}
                <div className="flex-1 flex flex-col">
                    {/* Title */}
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
                    
                    {/* Footer with ingredients */}
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {t('recipe.ingredients', lang).toLowerCase()}</span>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
};

export default RecipeCard;
