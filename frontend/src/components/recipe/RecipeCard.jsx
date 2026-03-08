import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChefHat, Globe, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import FavoriteButton from '@/components/common/FavoriteButton';

/**
 * RecipeCard - Language-aware recipe card with semantic design tokens
 */
export const RecipeCard = ({ recipe, variant = 'default', deferFavoriteCheck = false }) => {
    const { t: i18nT } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    
    const translations = recipe.translations || {};
    const langTranslation = translations[lang] || {};
    
    const hasTranslation = langTranslation.status === 'ready' && 
                          (langTranslation.recipe_name || langTranslation.title);
    
    const title = hasTranslation
        ? (langTranslation.recipe_name || langTranslation.title)
        : (recipe.recipe_name || recipe.title_original || recipe.title_translated?.en || 'Unknown Recipe');
    
    const description = hasTranslation
        ? (langTranslation.history_summary || langTranslation.characteristic_profile || langTranslation.description || '')
        : (recipe.history_summary || recipe.characteristic_profile || recipe.origin_story || '');
    
    const levelColors = {
        1: 'bg-primary text-primary-foreground',
        2: 'bg-secondary text-secondary-foreground',
        3: 'bg-accent text-accent-foreground',
        4: 'bg-gray-500 text-white',
        5: 'bg-gray-400 text-white',
    };
    
    const metadata = recipe.metadata || recipe;
    const country = metadata.origin_country || recipe.origin_country || recipe.country || 'Unknown';
    const region = metadata.origin_region || recipe.origin_region || recipe.region || '';
    const authenticityLevel = metadata.authenticity_level || recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;
    const slug = recipe.slug;
    const ingredientCount = recipe.content?.ingredients?.length || recipe.ingredients?.length || 0;
    
    const levelLabel = t(`badges.${authenticityLevel === 1 ? 'officiallyRecognized' : authenticityLevel === 2 ? 'traditionVerified' : 'traditional'}`, lang);
    const countryName = i18nT(`countries.${country}`, { defaultValue: country });
    
    const photos = metadata.photos || recipe.photos;
    const photoUrl = (photos && photos.length > 0 && photos[0].image_url)
        ? photos[0].image_url 
        : (recipe.image_url || null);

    // Editorial variant
    if (variant === 'editorial') {
        return (
            <Link to={getLocalizedPath(`/recipe/${slug}`)} data-testid={`recipe-card-${slug}`}>
                <article className="recipe-card-hover group h-full bg-card border border-border hover:border-primary overflow-hidden">
                    <div className="relative overflow-hidden h-40 sm:h-56 bg-muted">
                        {photoUrl ? (
                            <img 
                                src={photoUrl} 
                                alt={title}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                loading="lazy"
                            />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-muted-foreground/40 text-4xl font-light" style={{ fontFamily: 'var(--font-heading)' }}>SCL</span>
                            </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-foreground/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                        <div className="absolute top-2 left-2 sm:top-3 sm:left-3 z-10">
                            <FavoriteButton slug={slug} size="sm" deferStatusCheck={deferFavoriteCheck} />
                        </div>
                    </div>
                    
                    <div className="p-4 sm:p-6">
                        <span className="inline-block text-[10px] sm:text-xs uppercase tracking-widest text-primary mb-2 sm:mb-3">
                            {levelLabel}
                        </span>
                        
                        <p className="text-[10px] sm:text-xs text-muted-foreground mb-1.5 sm:mb-2 tracking-wide">
                            {countryName}{region ? ` · ${region}` : ''}
                        </p>
                        
                        <h3 className="text-base sm:text-lg font-light text-foreground group-hover:text-primary transition-colors line-clamp-2 mb-2 sm:mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {title}
                        </h3>
                        
                        {recipe.average_rating > 0 && (
                            <div className="flex items-center gap-2 text-[10px] sm:text-xs text-muted-foreground">
                                <Star className="h-3 w-3 fill-accent text-accent" />
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
                <div className="relative overflow-hidden rounded-sm mb-4 h-48 bg-muted">
                    {photoUrl ? (
                        <img 
                            src={photoUrl} 
                            alt={title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <ChefHat className="h-16 w-16 text-accent/30" />
                        </div>
                    )}
                    
                    <Badge className={`absolute top-3 right-3 ${levelColors[authenticityLevel] || levelColors[3]}`}>
                        <Star className="h-3 w-3 mr-1" />
                        {levelLabel}
                    </Badge>

                    <div className="absolute top-3 left-3 z-10">
                        <FavoriteButton slug={slug} size="sm" />
                    </div>
                </div>
                
                <div className="flex-1 flex flex-col">
                    <h3 className="text-xl font-semibold mb-2 text-foreground group-hover:text-primary transition-colors line-clamp-2">
                        {title}
                    </h3>
                    
                    <p className="text-sm text-muted-foreground mb-3 flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {countryName}{region ? ` • ${region}` : ''}
                    </p>
                    
                    {description && (
                        <p className="narrative-text text-sm line-clamp-3 flex-1">
                            {description.substring(0, 150)}{description.length > 150 ? '...' : ''}
                        </p>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-border text-sm text-muted-foreground">
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
