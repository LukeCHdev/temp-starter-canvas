import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI, translationAPI, aiAPI } from '@/utils/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { RecipeSEO } from '@/components/seo/SEOHelmet';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';
import { ReviewSection } from '@/components/recipe/ReviewSection';
import { FallbackBanner, TranslationPendingBanner, TranslationFailedBanner } from '@/components/common/FallbackBanner';
import { Skeleton } from '@/components/ui/skeleton';
import FavoriteButton from '@/components/common/FavoriteButton';
import { useRecipe } from '@/hooks/useRecipe';
import RelatedRecipes from '@/components/recipe/RelatedRecipes';
import { 
    ChefHat, 
    Globe, 
    Wine, 
    AlertTriangle, 
    Lightbulb, 
    BookOpen,
    ExternalLink,
    Youtube,
    Star,
    Minus,
    Plus,
    Loader2,
    RotateCcw
} from 'lucide-react';

// Skeleton component for recipe loading
const RecipeSkeleton = ({ language }) => {
    const loadingMessages = {
        en: 'Loading recipe...',
        it: 'Caricamento ricetta...',
        fr: 'Chargement de la recette...',
        es: 'Cargando receta...',
        de: 'Rezept wird geladen...'
    };
    
    const translatingMessages = {
        en: 'Preparing content in your language...',
        it: 'Preparazione contenuti nella tua lingua...',
        fr: 'Préparation du contenu dans votre langue...',
        es: 'Preparando contenido en tu idioma...',
        de: 'Inhalte in Ihrer Sprache werden vorbereitet...'
    };
    
    return (
        <div className="min-h-screen bg-background">
            {/* Hero Section Skeleton */}
            <section className="bg-gradient-to-b from-muted to-background py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    <div className="flex gap-2 mb-4">
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-6 w-24" />
                    </div>
                    <Skeleton className="h-12 w-3/4 mb-4" />
                    <div className="flex gap-4">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-4 w-16" />
                    </div>
                </div>
            </section>
            
            {/* Content Skeleton */}
            <section className="max-w-4xl mx-auto px-4 py-12 space-y-8">
                <div className="text-center py-8">
                    <ChefHat className="h-12 w-12 mx-auto text-primary animate-pulse mb-4" />
                    <p className="text-foreground/70">{loadingMessages[language] || loadingMessages.en}</p>
                    <p className="text-sm text-foreground/50 mt-2">{translatingMessages[language] || translatingMessages.en}</p>
                </div>
                
                <Card className="card-elegant">
                    <CardHeader><Skeleton className="h-6 w-48" /></CardHeader>
                    <CardContent>
                        <Skeleton className="h-4 w-full mb-2" />
                        <Skeleton className="h-4 w-full mb-2" />
                        <Skeleton className="h-4 w-3/4" />
                    </CardContent>
                </Card>
                
                <Card className="card-elegant">
                    <CardHeader><Skeleton className="h-6 w-32" /></CardHeader>
                    <CardContent>
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex justify-between py-2 border-b border-dashed border-accent/30">
                                <Skeleton className="h-4 w-32" />
                                <Skeleton className="h-4 w-20" />
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </section>
        </div>
    );
};

const RecipePage = () => {
    const { slug } = useParams();
    const location = useLocation();
    const { language, getLocalizedPath } = useLanguage();
    const { t, i18n } = useTranslation();
    
    useEffect(() => {
        const pathSegments = location.pathname.split('/').filter(Boolean);
        const urlLang = pathSegments[0];
        if (SUPPORTED_LANGUAGES[urlLang] && urlLang !== i18n.language) {
            i18n.changeLanguage(urlLang);
        }
    }, [location.pathname, i18n]);

    const currentLang = useMemo(() => language || 'en', [language]);

    const { data: queryData, isLoading: loading, isError, error: queryError } = useRecipe(slug, currentLang);
    const recipe = queryData?.recipe || null;
    const translationStatus = queryData?.translationStatus || null;
    const contentLanguage = queryData?.contentLanguage || null;

    // Scaling state
    const DEFAULT_SERVINGS = 4;
    const [servings, setServings] = useState(DEFAULT_SERVINGS);
    const [baseServings, setBaseServings] = useState(DEFAULT_SERVINGS);
    const [scaledIngredients, setScaledIngredients] = useState(null);
    const [isScaling, setIsScaling] = useState(false);
    const [scalingError, setScalingError] = useState(null);
    const [originalIngredients, setOriginalIngredients] = useState(null);

    useEffect(() => {
        if (recipe) {
            const recipeBaseServings = recipe.servings_default || recipe.servings || DEFAULT_SERVINGS;
            setBaseServings(recipeBaseServings);
            setServings(recipeBaseServings);
            setScaledIngredients(null);
            setOriginalIngredients(null);
            setScalingError(null);
        }
    }, [recipe?.slug]);

    const handleScale = useCallback(async (targetServings) => {
        if (!recipe?.slug || targetServings < 1 || targetServings > 50) return;
        
        if (targetServings === baseServings && originalIngredients) {
            setServings(baseServings);
            setScaledIngredients(null);
            setScalingError(null);
            return;
        }
        
        setIsScaling(true);
        setServings(targetServings);
        setScalingError(null);
        
        try {
            const response = await aiAPI.scale(recipe.slug, targetServings);
            
            if (response.data?.success && response.data?.recipe) {
                const scaledRecipe = response.data.recipe;
                if (!originalIngredients) {
                    setOriginalIngredients(recipe.ingredients);
                }
                const scaledIngs = scaledRecipe.translations?.[currentLang]?.ingredients 
                    || scaledRecipe.ingredients;
                setScaledIngredients(scaledIngs);
            }
        } catch (error) {
            console.error('Scaling error:', error);
            setScalingError(t('recipe.scalingError') || 'Could not update servings');
            toast.error(t('recipe.scalingError') || 'Could not update servings');
            setServings(baseServings);
        } finally {
            setIsScaling(false);
        }
    }, [recipe?.slug, baseServings, originalIngredients, currentLang, t]);

    const incrementServings = useCallback(() => {
        const newServings = Math.min(servings + 1, 50);
        handleScale(newServings);
    }, [servings, handleScale]);

    const decrementServings = useCallback(() => {
        const newServings = Math.max(servings - 1, 1);
        handleScale(newServings);
    }, [servings, handleScale]);

    const resetServings = useCallback(() => {
        setServings(baseServings);
        setScaledIngredients(null);
        setScalingError(null);
    }, [baseServings]);

    const getAuthenticityBadgeColor = (level) => {
        switch(level) {
            case 1: return 'bg-primary text-primary-foreground';
            case 2: return 'bg-secondary text-secondary-foreground';
            case 3: return 'bg-accent text-accent-foreground';
            case 4: return 'bg-gray-500 text-white';
            default: return 'bg-gray-400 text-white';
        }
    };

    const getAuthenticityLabel = (level) => {
        switch(level) {
            case 1: return t('recipe.official');
            case 2: return t('recipe.traditional');
            case 3: return t('recipe.localSource');
            case 4: return t('recipe.widelyRecognized');
            default: return t('recipe.modernAdapted');
        }
    };

    const renderLanguageBanner = () => {
        if (!contentLanguage || contentLanguage === currentLang) return null;
        if (translationStatus === 'pending') return <TranslationPendingBanner requestedLang={currentLang} />;
        if (translationStatus === 'failed') return <TranslationFailedBanner contentLang={contentLanguage} requestedLang={currentLang} />;
        return <FallbackBanner contentLang={contentLanguage} requestedLang={currentLang} />;
    };

    if (loading) return <RecipeSkeleton language={currentLang} />;

    if (isError) {
        return (
            <div className="min-h-screen flex items-center justify-center px-4" data-testid="error-state">
                <div className="text-center max-w-sm">
                    <AlertTriangle className="h-10 w-10 mx-auto text-destructive mb-4" />
                    <p className="text-lg text-foreground/70 mb-2">{t('recipe.loadError') || 'Failed to load recipe'}</p>
                    <p className="text-sm text-foreground/50 mb-4">{queryError?.message || ''}</p>
                    <Link to={getLocalizedPath('/')} className="text-primary hover:underline text-sm">
                        {t('recipe.returnHome')}
                    </Link>
                </div>
            </div>
        );
    }

    if (!recipe) {
        return (
            <div className="min-h-screen flex items-center justify-center px-4" data-testid="not-found-state">
                <div className="text-center">
                    <p className="text-lg sm:text-xl text-foreground/70 mb-4">{t('recipe.notFound')}</p>
                    <Link to={getLocalizedPath('/')} className="text-primary hover:underline">
                        {t('recipe.returnHome')}
                    </Link>
                </div>
            </div>
        );
    }

    const recipeName = recipe.recipe_name || recipe.title_original || recipe.title_translated?.en || 'Unknown Recipe';
    const country = recipe.origin_country || recipe.country || 'Unknown';
    const region = recipe.origin_region || recipe.region || 'Unknown';
    const authenticityLevel = recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;

    const translation = recipe.translations?.[currentLang];
    const isTranslated = translation?.status === 'ready';
    
    const getTranslatedContent = (translationKey, fallbackKey) => {
        if (isTranslated && translation?.[translationKey]) {
            return { content: translation[translationKey], isTranslated: true };
        }
        return { content: recipe[fallbackKey], isTranslated: false };
    };
    
    const historyContent = getTranslatedContent('history_and_origin', 'history_summary');
    const profileContent = getTranslatedContent('characteristic_profile', 'characteristic_profile');
    const noNoRulesContent = isTranslated && translation?.no_no_rules?.length > 0 
        ? { content: translation.no_no_rules, isTranslated: true }
        : { content: recipe.no_no_rules, isTranslated: false };
    const techniquesContent = isTranslated && translation?.special_techniques?.length > 0
        ? { content: translation.special_techniques, isTranslated: true }
        : { content: recipe.special_techniques, isTranslated: false };
    const ingredientsContent = isTranslated && translation?.ingredients?.length > 0
        ? { content: translation.ingredients, isTranslated: true }
        : { content: recipe.ingredients, isTranslated: false };
    const instructionsContent = isTranslated && translation?.instructions?.length > 0
        ? { content: translation.instructions, isTranslated: true }
        : { content: recipe.instructions, isTranslated: false };
    const winePairingContent = isTranslated && translation?.wine_pairing
        ? { content: translation.wine_pairing, isTranslated: true }
        : { content: recipe.wine_pairing, isTranslated: false };

    return (
        <div className="min-h-screen" data-testid="recipe-page">
            <RecipeSEO recipe={recipe} slug={slug} />
            
            {/* Hero Section */}
            <section className="bg-gradient-to-b from-muted to-background py-6 sm:py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    {renderLanguageBanner()}
                    
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-3 sm:mb-4">
                        <Badge className={`text-[10px] sm:text-xs ${getAuthenticityBadgeColor(authenticityLevel)}`}>
                            <Star className="h-3 w-3 mr-1" />
                            {t('recipe.level')} {authenticityLevel}: {getAuthenticityLabel(authenticityLevel)}
                        </Badge>
                        {recipe.gpt_used && (
                            <Badge variant="outline" className="border-accent text-accent text-[10px] sm:text-xs">
                                <ChefHat className="h-3 w-3 mr-1" />
                                {recipe.gpt_used}
                            </Badge>
                        )}
                    </div>
                    
                    <div className="flex items-start justify-between gap-3">
                        <h1 className="text-2xl sm:text-4xl lg:text-5xl font-light mb-3 sm:mb-4 text-foreground break-words min-w-0 tracking-tight" 
                            style={{ fontFamily: 'var(--font-heading)' }}>
                            {recipeName}
                        </h1>
                        <div className="flex-shrink-0 pt-1">
                            <FavoriteButton slug={recipe.slug} />
                        </div>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm sm:text-base text-foreground/70">
                        <span className="flex items-center gap-1">
                            <Globe className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                            {t(`countries.${country}`, { defaultValue: country })}
                        </span>
                        <span className="hidden sm:inline">·</span>
                        <span>{region}</span>
                    </div>
                </div>
            </section>

            {/* Recipe Hero Image */}
            {recipe.image_url && (
                <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 -mt-1 sm:-mt-2 mb-4" data-testid="recipe-hero-image">
                    <div className="relative overflow-hidden rounded-lg shadow-md aspect-[4/3] sm:aspect-video bg-muted">
                        <img
                            src={recipe.image_url}
                            alt={recipe.image_alt || recipeName}
                            className="w-full h-full object-cover"
                            loading="eager"
                        />
                        {recipe.image_metadata?.photographer && (
                            <div className="absolute bottom-0 right-0 bg-black/50 text-white text-[10px] sm:text-xs px-2 py-1 rounded-tl">
                                {recipe.image_metadata.photographer_url ? (
                                    <a
                                        href={recipe.image_metadata.photographer_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="hover:underline"
                                        data-testid="photographer-credit"
                                    >
                                        {recipe.image_metadata.photographer} / Unsplash
                                    </a>
                                ) : (
                                    <span>{recipe.image_metadata.photographer} / Unsplash</span>
                                )}
                            </div>
                        )}
                    </div>
                </section>
            )}

            {/* Main Content */}
            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-12 space-y-6 sm:space-y-8">
                
                {/* History & Character */}
                {(historyContent.content || recipe.origin_story) && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
                                {t('recipe.history')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed text-sm sm:text-base break-words">
                                {historyContent.content || recipe.origin_story}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {profileContent.content && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <ChefHat className="h-4 w-4 sm:h-5 sm:w-5 text-secondary" />
                                {t('recipe.profile')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed text-sm sm:text-base break-words">
                                {profileContent.content}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* No-No Rules */}
                {noNoRulesContent.content && noNoRulesContent.content.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-destructive">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg text-destructive" style={{ fontFamily: 'var(--font-heading)' }}>
                                <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5" />
                                {t('recipe.noNoRules')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {noNoRulesContent.content.map((rule, index) => (
                                    <li key={index} className="flex items-start gap-2 text-destructive text-sm sm:text-base">
                                        <span className="font-bold flex-shrink-0">✗</span>
                                        <span className="break-words min-w-0">{rule}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Special Techniques */}
                {techniquesContent.content && techniquesContent.content.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-accent">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <Lightbulb className="h-4 w-4 sm:h-5 sm:w-5 text-accent" />
                                {t('recipe.techniques')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {techniquesContent.content.map((technique, index) => (
                                    <li key={index} className="flex items-start gap-2 text-sm sm:text-base">
                                        <span className="text-accent font-bold flex-shrink-0">★</span>
                                        <span className="italic break-words min-w-0">{technique}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Technique Guides */}
                {recipe.technique_links && recipe.technique_links.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-secondary">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-secondary" />
                                {t('recipe.techniqueGuides')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3 sm:space-y-4">
                                {recipe.technique_links.map((link, index) => (
                                    <div key={index} className="bg-muted rounded-lg p-3 sm:p-4">
                                        <h4 className="font-semibold text-foreground mb-1 text-sm sm:text-base break-words">{link.technique}</h4>
                                        {link.description && (
                                            <p className="text-xs sm:text-sm text-foreground/70 mb-2 break-words">{link.description}</p>
                                        )}
                                        {link.url && (
                                            <a 
                                                href={link.url} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1 text-xs sm:text-sm text-primary hover:underline touch-manipulation"
                                            >
                                                <ExternalLink className="h-3 w-3" />
                                                {t('recipe.watchTutorial')}
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Ingredients with Serving Selector */}
                {ingredientsContent.content && ingredientsContent.content.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader className="pb-2 sm:pb-4">
                            <div className="flex flex-col gap-3">
                                <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                    <span>🧺</span> {t('recipe.ingredients')}
                                </CardTitle>
                                
                                <div className="flex items-center gap-2 sm:gap-3 bg-muted rounded-lg px-3 py-2 self-start" data-testid="serving-selector">
                                    <span className="text-xs sm:text-sm text-muted-foreground font-medium whitespace-nowrap">
                                        {t('recipe.servings')}:
                                    </span>
                                    <div className="flex items-center gap-1">
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-9 w-9 sm:h-8 sm:w-8 rounded-full border-primary text-primary hover:bg-primary hover:text-primary-foreground disabled:opacity-50 touch-manipulation"
                                            onClick={decrementServings}
                                            disabled={servings <= 1 || isScaling}
                                            aria-label="Decrease servings"
                                            data-testid="serving-decrease"
                                        >
                                            <Minus className="h-4 w-4" />
                                        </Button>
                                        
                                        <span className="w-10 text-center font-semibold text-foreground text-lg tabular-nums" data-testid="serving-count">
                                            {isScaling ? (
                                                <Loader2 className="h-5 w-5 animate-spin mx-auto text-primary" />
                                            ) : (
                                                servings
                                            )}
                                        </span>
                                        
                                        <Button
                                            variant="outline"
                                            size="icon"
                                            className="h-9 w-9 sm:h-8 sm:w-8 rounded-full border-primary text-primary hover:bg-primary hover:text-primary-foreground disabled:opacity-50 touch-manipulation"
                                            onClick={incrementServings}
                                            disabled={servings >= 50 || isScaling}
                                            aria-label="Increase servings"
                                            data-testid="serving-increase"
                                        >
                                            <Plus className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    
                                    {servings !== baseServings && (
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            className="h-9 w-9 sm:h-8 sm:w-8 p-0 text-primary hover:bg-primary/10 touch-manipulation"
                                            onClick={resetServings}
                                            disabled={isScaling}
                                            aria-label="Reset to original"
                                            data-testid="serving-reset"
                                        >
                                            <RotateCcw className="h-4 w-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                            
                            {servings !== baseServings && !isScaling && (
                                <p className="text-xs text-primary mt-2">
                                    {t('recipe.scaledFrom')} {baseServings} → {servings} {t('recipe.servings').toLowerCase()}
                                </p>
                            )}

                            {scalingError && (
                                <p className="text-xs text-destructive mt-2 flex items-center gap-1" data-testid="scaling-error">
                                    <AlertTriangle className="h-3 w-3" />
                                    {scalingError}
                                </p>
                            )}
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-0">
                                {(scaledIngredients || ingredientsContent.content).map((ing, index) => (
                                    <div 
                                        key={index} 
                                        className={`flex flex-col sm:flex-row sm:items-center sm:justify-between py-2.5 sm:py-2 border-b border-dashed border-accent/30 last:border-0 transition-all duration-200 ${
                                            ing._scaled ? 'bg-primary/5 -mx-2 px-2 rounded' : ''
                                        }`}
                                        data-testid={`ingredient-${index}`}
                                    >
                                        <span className="font-medium text-sm sm:text-base text-foreground break-words min-w-0">{ing.item}</span>
                                        <span className={`text-sm sm:text-base tabular-nums flex-shrink-0 ${ing._scaled ? 'font-semibold text-primary' : 'text-foreground/70'}`}>
                                            {ing.amount} {ing.unit}
                                            {ing.notes && <span className="italic text-xs sm:text-sm ml-1 sm:ml-2 text-foreground/50">({ing.notes})</span>}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Instructions */}
                {instructionsContent.content && instructionsContent.content.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <span>👨‍🍳</span> {t('recipe.instructions')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ol className="space-y-4">
                                {instructionsContent.content.map((step, index) => (
                                    <li key={index} className="flex gap-3 sm:gap-4">
                                        <span className="flex-shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs sm:text-sm">
                                            {index + 1}
                                        </span>
                                        <p className="pt-0.5 sm:pt-1 text-sm sm:text-base narrative-text break-words min-w-0">{typeof step === 'string' ? step : step.instruction}</p>
                                    </li>
                                ))}
                            </ol>
                        </CardContent>
                    </Card>
                )}

                {/* Wine Pairing */}
                {winePairingContent.content?.recommended_wines?.length > 0 && (
                    <Card className="card-elegant bg-gradient-to-br from-primary/5 to-primary/10">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-primary" style={{ fontFamily: 'var(--font-heading)' }}>
                                <Wine className="h-5 w-5" />
                                {t('recipe.winePairing')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                                {winePairingContent.content.recommended_wines.map((wine, index) => (
                                    <div key={index} className="bg-card/80 rounded-lg p-3 sm:p-4 shadow-sm">
                                        <h4 className="font-semibold text-primary text-sm sm:text-base">{wine.name}</h4>
                                        <p className="text-xs sm:text-sm text-foreground/60 mb-1.5 sm:mb-2">{wine.region}</p>
                                        <p className="text-xs sm:text-sm italic">{wine.reason}</p>
                                    </div>
                                ))}
                            </div>
                            {winePairingContent.content.notes && (
                                <p className="mt-4 text-sm text-foreground/70 italic border-t pt-3">
                                    {winePairingContent.content.notes}
                                </p>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Sources */}
                {recipe.original_source_urls && recipe.original_source_urls.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-sm sm:text-base" style={{ fontFamily: 'var(--font-heading)' }}>
                                <ExternalLink className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                                {t('recipe.originalSources')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.original_source_urls.map((source, index) => (
                                    <li key={index} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 text-sm">
                                        <Badge variant="outline" className="text-[10px] sm:text-xs w-fit flex-shrink-0">
                                            {source.type || t('recipe.source')}
                                        </Badge>
                                        {source.url && source.url !== 'unknown' ? (
                                            <a href={source.url} target="_blank" rel="noopener noreferrer" 
                                               className="text-primary hover:underline truncate min-w-0 touch-manipulation">
                                                {source.url}
                                            </a>
                                        ) : (
                                            <span className="text-foreground/50">{t('recipe.source')}</span>
                                        )}
                                        {source.language && (
                                            <span className="text-[10px] sm:text-xs text-foreground/50 uppercase">({source.language})</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* YouTube Links */}
                {recipe.youtube_links && recipe.youtube_links.length > 0 && recipe.youtube_links[0].url && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base sm:text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                <Youtube className="h-4 w-4 sm:h-5 sm:w-5 text-destructive" />
                                {t('recipe.videoTutorials')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.youtube_links.filter(link => link.url).map((link, index) => (
                                    <li key={index}>
                                        <a href={link.url} target="_blank" rel="noopener noreferrer"
                                           className="text-primary hover:underline flex items-center gap-2 text-sm sm:text-base py-1 touch-manipulation">
                                            <Youtube className="h-4 w-4 flex-shrink-0" />
                                            <span className="break-words min-w-0">{link.title || t('recipe.watchVideo')}</span>
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Related Recipes */}
                <RelatedRecipes recipe={recipe} lang={currentLang} />

                {/* Ratings & Reviews Section */}
                <ReviewSection 
                    slug={slug} 
                    initialRating={recipe.average_rating || 0}
                    initialCount={recipe.ratings_count || 0}
                />

                {/* Metadata */}
                <div className="text-center text-xs sm:text-sm text-foreground/50 pt-6 sm:pt-8 border-t">
                    {recipe.date_fetched && (
                        <p>{t('recipe.recipeAdded')}: {new Date(recipe.date_fetched).toLocaleDateString()}</p>
                    )}
                    {recipe.collection_method && (
                        <p className="mt-1">
                            {t('recipe.source')}: {recipe.collection_method === 'ai_expansion' ? t('recipe.aiGenerated') : 
                                    recipe.collection_method === 'csv_import' ? t('recipe.imported') : 
                                    recipe.collection_method}
                        </p>
                    )}
                </div>
            </section>
        </div>
    );
};

export default RecipePage;
