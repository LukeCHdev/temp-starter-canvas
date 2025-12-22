import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Clock, ChefHat, Globe, Star, Loader2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

/**
 * TranslatedRecipeCard - Displays recipe content based on translation status
 * 
 * Implements approved architecture:
 * - status='ready': Show translated content
 * - status='pending': Show localized placeholder
 * - status='failed': Show localized error placeholder
 */
export const TranslatedRecipeCard = ({ recipe }) => {
    const { t, i18n } = useTranslation();
    
    const { status, content, metadata, slug } = recipe;
    
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
    
    const currentLang = i18n.language?.slice(0, 2) || 'en';
    const authenticityLevel = metadata?.authenticity_level || 3;
    const levelLabel = levelLabels[authenticityLevel]?.[currentLang] || levelLabels[authenticityLevel]?.en || 'Traditional';
    
    // Get photo URL
    const photoUrl = metadata?.photos?.[0]?.image_url || null;
    
    // Render content based on status
    const renderContent = () => {
        if (status === 'ready' && content) {
            // Translation ready - show content
            const title = content.recipe_name || 'Unknown Recipe';
            const description = content.history_summary || content.characteristic_profile || '';
            const ingredientCount = content.ingredients?.length || 0;
            
            return (
                <>
                    <h3 className="text-xl font-semibold mb-2 text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors line-clamp-2">
                        {title}
                    </h3>
                    
                    <p className="text-sm text-[#1E1E1E]/60 mb-3 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {metadata?.origin_country || 'Unknown'} • {metadata?.origin_region || 'Unknown'}
                    </p>
                    
                    {description && (
                        <p className="narrative-text text-sm line-clamp-3 flex-1">
                            {description.substring(0, 150)}{description.length > 150 ? '...' : ''}
                        </p>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-[#E5DCC3] flex items-center justify-between text-sm text-[#1E1E1E]/60">
                        {ingredientCount > 0 && (
                            <span>{ingredientCount} {t('recipe.ingredients')}</span>
                        )}
                    </div>
                </>
            );
        }
        
        if (status === 'pending') {
            // Translation in progress - show placeholder
            return (
                <div className="flex flex-col items-center justify-center h-full py-8">
                    <Loader2 className="h-8 w-8 text-[#6A1F2E] animate-spin mb-3" />
                    <p className="text-sm text-[#1E1E1E]/60 text-center">
                        {t('recipe.translating')}
                    </p>
                    <p className="text-xs text-[#1E1E1E]/40 mt-2">
                        {metadata?.origin_country || ''}
                    </p>
                </div>
            );
        }
        
        if (status === 'failed') {
            // Translation failed - show error placeholder
            return (
                <div className="flex flex-col items-center justify-center h-full py-8">
                    <ChefHat className="h-8 w-8 text-[#CBA55B]/50 mb-3" />
                    <p className="text-sm text-[#1E1E1E]/60 text-center">
                        {t('recipe.translationUnavailable')}
                    </p>
                    <p className="text-xs text-[#1E1E1E]/40 mt-2">
                        {metadata?.origin_country || ''}
                    </p>
                </div>
            );
        }
        
        // Fallback
        return (
            <div className="flex flex-col items-center justify-center h-full py-8">
                <Loader2 className="h-8 w-8 text-[#6A1F2E] animate-spin mb-3" />
                <p className="text-sm text-[#1E1E1E]/60">
                    {t('recipe.loadingRecipe')}
                </p>
            </div>
        );
    };
    
    return (
        <Link to={`/recipe/${slug}`} data-testid={`recipe-card-${slug}`}>
            <Card className="card-elegant group cursor-pointer h-full flex flex-col">
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-[#F5F2E8]">
                    {photoUrl ? (
                        <img 
                            src={photoUrl} 
                            alt={content?.recipe_name || 'Recipe'}
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
                    {renderContent()}
                </div>
            </Card>
        </Link>
    );
};

export default TranslatedRecipeCard;
