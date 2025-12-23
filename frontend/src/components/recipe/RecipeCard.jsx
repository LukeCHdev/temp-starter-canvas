import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star, AlertCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';

/**
 * RecipeCard - Language-aware recipe card that shows content in the current language
 * 
 * Features:
 * - Automatically uses translations if available
 * - Shows fallback indicator when displaying non-requested language
 * - Localized badges and labels
 * - No hardcoded "Test Data" badges
 */
export const RecipeCard = ({ recipe }) => {
    const { t } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    const currentLang = language || 'en';
    
    // Authenticity level styling
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
    
    // Localized ingredient labels
    const ingredientLabels = {
        en: 'ingredients',
        it: 'ingredienti',
        fr: 'ingrédients',
        es: 'ingredientes',
        de: 'Zutaten'
    };
    
    // Fallback content messages
    const fallbackMessages = {
        en: 'Shown in English',
        it: 'Mostrato in inglese',
        fr: 'Affiché en anglais',
        es: 'Mostrado en inglés',
        de: 'Auf Englisch angezeigt'
    };
    
    // Determine content source and language
    let title, description, contentLang, isTranslated;
    
    // Check if recipe has translations structure (from translation API)
    if (recipe.content && recipe.status === 'ready') {
        // Using TranslatedRecipeCard format
        title = recipe.content.recipe_name || recipe.content.title || 'Unknown Recipe';
        description = recipe.content.history_summary || recipe.content.characteristic_profile || '';
        contentLang = recipe.lang || currentLang;
        isTranslated = true;
    } else if (recipe.translations && recipe.translations[currentLang]?.status === 'ready') {
        // Recipe has embedded translations
        const trans = recipe.translations[currentLang];
        title = trans.recipe_name || trans.title || recipe.recipe_name || 'Unknown Recipe';
        description = trans.history_summary || trans.characteristic_profile || recipe.history_summary || '';
        contentLang = currentLang;
        isTranslated = true;
    } else if (recipe._translated && recipe._display_lang === currentLang) {
        // Recipe was translated on-the-fly
        title = recipe.recipe_name || recipe.title_original || 'Unknown Recipe';
        description = recipe.history_summary || recipe.characteristic_profile || '';
        contentLang = currentLang;
        isTranslated = true;
    } else {
        // Use original content (fallback)
        title = recipe.recipe_name || recipe.title_translated?.en || recipe.title_original || 'Unknown Recipe';
        description = recipe.history_summary || recipe.characteristic_profile || recipe.origin_story || '';
        contentLang = recipe.content_language?.slice(0, 2) || 'en';
        isTranslated = false;
    }
    
    // Get metadata
    const metadata = recipe.metadata || recipe;
    const country = metadata.origin_country || recipe.origin_country || recipe.country || 'Unknown';
    const region = metadata.origin_region || recipe.origin_region || recipe.region || '';
    const authenticityLevel = metadata.authenticity_level || recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;
    const slug = recipe.slug;
    const ingredientCount = recipe.content?.ingredients?.length || recipe.ingredients?.length || 0;
    
    // Get localized label
    const levelLabel = levelLabels[authenticityLevel]?.[currentLang] || levelLabels[authenticityLevel]?.en || levelLabels[3][currentLang];
    
    // Translate country name
    const countryName = t(`countries.${country}`, { defaultValue: country });
    
    // Get photo if available
    const photos = metadata.photos || recipe.photos;
    const photoUrl = photos && photos.length > 0 && photos[0].image_url 
        ? photos[0].image_url 
        : null;
    
    // Determine if we need to show fallback warning
    const showFallbackWarning = !isTranslated && currentLang !== 'en' && contentLang !== currentLang;

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
                    {/* Fallback warning if showing non-requested language */}
                    {showFallbackWarning && (
                        <div className="flex items-center gap-1 text-xs text-amber-600 mb-2">
                            <AlertCircle className="h-3 w-3" />
                            <span className="italic">{fallbackMessages[currentLang] || fallbackMessages.en}</span>
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
                            <span>{ingredientCount} {ingredientLabels[currentLang] || ingredientLabels.en}</span>
                        )}
                    </div>
                </div>
            </Card>
        </Link>
    );
};

export default RecipeCard;
