import React, { useEffect, useState, useMemo } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI, translationAPI } from '@/utils/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { RecipeSEO } from '@/components/seo/SEOHelmet';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';
import { ReviewSection } from '@/components/recipe/ReviewSection';
import { FallbackBanner, TranslationPendingBanner, TranslationFailedBanner } from '@/components/common/FallbackBanner';
import { Skeleton } from '@/components/ui/skeleton';
import { 
    ChefHat, 
    Globe, 
    Wine, 
    AlertTriangle, 
    Lightbulb, 
    BookOpen,
    ExternalLink,
    Youtube,
    Star
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
        <div className="min-h-screen bg-[#FAF7F0]">
            {/* Hero Section Skeleton */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
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
                    <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                    <p className="text-[#1E1E1E]/70">{loadingMessages[language] || loadingMessages.en}</p>
                    <p className="text-sm text-[#1E1E1E]/50 mt-2">{translatingMessages[language] || translatingMessages.en}</p>
                </div>
                
                {/* History Card Skeleton */}
                <Card className="card-elegant">
                    <CardHeader>
                        <Skeleton className="h-6 w-48" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton className="h-4 w-full mb-2" />
                        <Skeleton className="h-4 w-full mb-2" />
                        <Skeleton className="h-4 w-3/4" />
                    </CardContent>
                </Card>
                
                {/* Ingredients Skeleton */}
                <Card className="card-elegant">
                    <CardHeader>
                        <Skeleton className="h-6 w-32" />
                    </CardHeader>
                    <CardContent>
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="flex justify-between py-2 border-b border-dashed border-[#CBA55B]/30">
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
    const [recipe, setRecipe] = useState(null);
    const [translationStatus, setTranslationStatus] = useState(null);
    const [contentLanguage, setContentLanguage] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isTranslating, setIsTranslating] = useState(false);
    const { language, getLocalizedPath } = useLanguage();
    const { t, i18n } = useTranslation();

    // CRITICAL: Sync i18n with route language on every route change
    useEffect(() => {
        const pathSegments = location.pathname.split('/').filter(Boolean);
        const urlLang = pathSegments[0];
        
        if (SUPPORTED_LANGUAGES[urlLang] && urlLang !== i18n.language) {
            i18n.changeLanguage(urlLang);
        }
    }, [location.pathname, i18n]);

    // Use language from context - derived from URL
    const currentLang = useMemo(() => language || 'en', [language]);

    useEffect(() => {
        let isMounted = true;
        
        const loadRecipe = async () => {
            setLoading(true);
            setTranslationStatus(null);
            setContentLanguage(null);
            setRecipe(null); // CRITICAL: Clear recipe to prevent English flash
            setIsTranslating(false);
            
            try {
                // Step 1: Try the translation API first (fast, pre-translated content)
                const translationRes = await translationAPI.getRecipe(slug, currentLang);
                const translationData = translationRes.data;
                
                if (!isMounted) return;
                
                if (translationData.status === 'ready' && translationData.content) {
                    // Translation is ready - use it immediately
                    setRecipe({
                        ...translationData.content,
                        ...translationData.metadata,
                        slug: translationData.slug
                    });
                    setContentLanguage(translationData.lang);
                    setTranslationStatus('ready');
                    setLoading(false);
                    return;
                }
                
                // Step 2: Translation not ready - show skeleton and fetch with on-the-fly translation
                setIsTranslating(true);
                setTranslationStatus(translationData.status || 'pending');
                
                // Fetch with lang parameter - this will do on-the-fly translation
                const translatedRes = await recipeAPI.getBySlug(slug, currentLang);
                
                if (!isMounted) return;
                
                const recipeData = translatedRes.data;
                
                // CRITICAL: Only show recipe if content matches requested language
                const displayLang = recipeData._display_lang || recipeData.content_language || 'en';
                const actualLang = displayLang.slice(0, 2).toLowerCase();
                
                if (actualLang === currentLang || recipeData._translated) {
                    // Content is in the requested language
                    setRecipe(recipeData);
                    setContentLanguage(actualLang);
                    setTranslationStatus('ready');
                } else {
                    // Content is NOT in the requested language - show fallback banner
                    setRecipe(recipeData);
                    setContentLanguage(actualLang);
                    setTranslationStatus('fallback');
                }
                
            } catch (error) {
                console.error('Recipe fetch error:', error);
                
                if (!isMounted) return;
                
                // Final fallback - try to get any recipe content
                try {
                    const fallbackRes = await recipeAPI.getBySlug(slug, 'en');
                    if (isMounted) {
                        setRecipe(fallbackRes.data);
                        setContentLanguage('en');
                        setTranslationStatus('failed');
                    }
                } catch (finalError) {
                    if (isMounted) {
                        toast.error(t('recipe.notFound'));
                    }
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                    setIsTranslating(false);
                }
            }
        };

        loadRecipe();
        
        return () => {
            isMounted = false;
        };
    }, [slug, currentLang, t]);

    // Authenticity helpers
    const getAuthenticityBadgeColor = (level) => {
        switch(level) {
            case 1: return 'bg-[#6A1F2E] text-white';
            case 2: return 'bg-[#3F4A3C] text-white';
            case 3: return 'bg-[#CBA55B] text-white';
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

    // Render appropriate banner based on translation status
    const renderLanguageBanner = () => {
        if (!contentLanguage || contentLanguage === currentLang) {
            return null;
        }
        
        if (translationStatus === 'pending') {
            return <TranslationPendingBanner requestedLang={currentLang} />;
        }
        
        if (translationStatus === 'failed') {
            return <TranslationFailedBanner contentLang={contentLanguage} requestedLang={currentLang} />;
        }
        
        // Default fallback banner
        return <FallbackBanner contentLang={contentLanguage} requestedLang={currentLang} />;
    };

    // CRITICAL: Show skeleton while loading OR while translating
    // This prevents showing English content before translated content is ready
    if (loading || (isTranslating && !recipe)) {
        return <RecipeSkeleton language={currentLang} />;
    }

    if (!recipe) {
        return (
            <div className="min-h-screen flex items-center justify-center" data-testid="not-found-state">
                <div className="text-center">
                    <p className="text-xl text-[#1E1E1E]/70 mb-4">{t('recipe.notFound')}</p>
                    <Link to={getLocalizedPath('/')} className="text-[#6A1F2E] hover:underline">
                        {t('recipe.returnHome')}
                    </Link>
                </div>
            </div>
        );
    }

    // Handle both old and new schema
    const recipeName = recipe.recipe_name || recipe.title_original || recipe.title_translated?.en || 'Unknown Recipe';
    const country = recipe.origin_country || recipe.country || 'Unknown';
    const region = recipe.origin_region || recipe.region || 'Unknown';
    const recipeLanguage = recipe.origin_language || recipe.original_language || 'en';
    const authenticityLevel = recipe.authenticity_level || recipe.source_validation?.authenticity_rank || 3;

    // TRANSLATION-AWARE CONTENT EXTRACTION
    // Check if translations exist for the current language and are ready
    const translation = recipe.translations?.[currentLang];
    const isTranslated = translation?.status === 'ready';
    
    // Helper function to get translated content with fallback
    const getTranslatedContent = (translationKey, fallbackKey) => {
        if (isTranslated && translation?.[translationKey]) {
            return { content: translation[translationKey], isTranslated: true };
        }
        return { content: recipe[fallbackKey], isTranslated: false };
    };
    
    // Extract content with translation awareness
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
    
    // Show fallback warning only if content is not translated and we're not on English
    const showContentFallback = currentLang !== 'en' && !isTranslated;

    return (
        <div className="min-h-screen" data-testid="recipe-page">
            {/* SEO Metadata */}
            <RecipeSEO recipe={recipe} slug={slug} />
            
            {/* Hero Section */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
                    {/* Language Fallback Banner */}
                    {renderLanguageBanner()}
                    
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                        <Badge className={getAuthenticityBadgeColor(authenticityLevel)}>
                            <Star className="h-3 w-3 mr-1" />
                            {t('recipe.level')} {authenticityLevel}: {getAuthenticityLabel(authenticityLevel)}
                        </Badge>
                        {recipe.gpt_used && (
                            <Badge variant="outline" className="border-[#CBA55B] text-[#CBA55B]">
                                <ChefHat className="h-3 w-3 mr-1" />
                                {recipe.gpt_used}
                            </Badge>
                        )}
                    </div>
                    
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 text-[#1E1E1E]" 
                        style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {recipeName}
                    </h1>
                    
                    <div className="flex flex-wrap items-center gap-4 text-[#1E1E1E]/70">
                        <span className="flex items-center gap-1">
                            <Globe className="h-4 w-4" />
                            {t(`countries.${country}`, { defaultValue: country })}
                        </span>
                        <span>•</span>
                        <span>{region}</span>
                        <span>•</span>
                        <span className="uppercase text-sm">{recipeLanguage}</span>
                    </div>
                </div>
            </section>

            {/* Main Content */}
            <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
                
                {/* History & Character */}
                {(historyContent.content || recipe.origin_story) && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <BookOpen className="h-5 w-5 text-[#6A1F2E]" />
                                {t('recipe.history')}
                                {showContentFallback && !historyContent.isTranslated && (
                                    <span className="text-xs font-normal text-amber-600 ml-2">(EN)</span>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed">
                                {historyContent.content || recipe.origin_story}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {profileContent.content && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <ChefHat className="h-5 w-5 text-[#3F4A3C]" />
                                {t('recipe.profile')}
                                {showContentFallback && !profileContent.isTranslated && (
                                    <span className="text-xs font-normal text-amber-600 ml-2">(EN)</span>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed">
                                {profileContent.content}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* No-No Rules */}
                {noNoRulesContent.content && noNoRulesContent.content.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-red-500">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-red-700" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <AlertTriangle className="h-5 w-5" />
                                {t('recipe.noNoRules')}
                                {showContentFallback && !noNoRulesContent.isTranslated && (
                                    <span className="text-xs font-normal text-amber-600 ml-2">(EN)</span>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {noNoRulesContent.content.map((rule, index) => (
                                    <li key={index} className="flex items-start gap-2 text-red-800">
                                        <span className="text-red-500 font-bold">✗</span>
                                        <span>{rule}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Special Techniques */}
                {recipe.special_techniques && recipe.special_techniques.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-[#CBA55B]">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <Lightbulb className="h-5 w-5 text-[#CBA55B]" />
                                {t('recipe.techniques')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.special_techniques.map((technique, index) => (
                                    <li key={index} className="flex items-start gap-2">
                                        <span className="text-[#CBA55B] font-bold">★</span>
                                        <span className="italic">{technique}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Technique Guides */}
                {recipe.technique_links && recipe.technique_links.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-[#3F4A3C]">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <BookOpen className="h-5 w-5 text-[#3F4A3C]" />
                                {t('recipe.techniqueGuides')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {recipe.technique_links.map((link, index) => (
                                    <div key={index} className="bg-[#F5F2E8] rounded-lg p-4">
                                        <h4 className="font-semibold text-[#1E1E1E] mb-1">{link.technique}</h4>
                                        {link.description && (
                                            <p className="text-sm text-[#1E1E1E]/70 mb-2">{link.description}</p>
                                        )}
                                        {link.url && (
                                            <a 
                                                href={link.url} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-1 text-sm text-[#6A1F2E] hover:underline"
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

                {/* Ingredients */}
                {recipe.ingredients && recipe.ingredients.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                🧺 {t('recipe.ingredients')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-3">
                                {recipe.ingredients.map((ing, index) => (
                                    <div key={index} className="flex items-center justify-between py-2 border-b border-dashed border-[#CBA55B]/30 last:border-0">
                                        <span className="font-medium">{ing.item}</span>
                                        <span className="text-[#1E1E1E]/70">
                                            {ing.amount} {ing.unit}
                                            {ing.notes && <span className="italic text-sm ml-2">({ing.notes})</span>}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Instructions */}
                {recipe.instructions && recipe.instructions.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                👨‍🍳 {t('recipe.instructions')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ol className="space-y-4">
                                {recipe.instructions.map((step, index) => (
                                    <li key={index} className="flex gap-4">
                                        <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-bold text-sm">
                                            {index + 1}
                                        </span>
                                        <p className="pt-1 narrative-text">{typeof step === 'string' ? step : step.instruction}</p>
                                    </li>
                                ))}
                            </ol>
                        </CardContent>
                    </Card>
                )}

                {/* Wine Pairing */}
                {recipe.wine_pairing && recipe.wine_pairing.recommended_wines && recipe.wine_pairing.recommended_wines.length > 0 && (
                    <Card className="card-elegant bg-gradient-to-br from-[#6A1F2E]/5 to-[#6A1F2E]/10">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-[#6A1F2E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <Wine className="h-5 w-5" />
                                {t('recipe.winePairing')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4">
                                {recipe.wine_pairing.recommended_wines.map((wine, index) => (
                                    <div key={index} className="bg-white/80 rounded-lg p-4 shadow-sm">
                                        <h4 className="font-semibold text-[#6A1F2E]">{wine.name}</h4>
                                        <p className="text-sm text-[#1E1E1E]/60 mb-2">{wine.region}</p>
                                        <p className="text-sm italic">{wine.reason}</p>
                                    </div>
                                ))}
                            </div>
                            {recipe.wine_pairing.notes && (
                                <p className="mt-4 text-sm text-[#1E1E1E]/70 italic border-t pt-3">
                                    {recipe.wine_pairing.notes}
                                </p>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Sources */}
                {recipe.original_source_urls && recipe.original_source_urls.length > 0 && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-sm" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <ExternalLink className="h-4 w-4" />
                                {t('recipe.originalSources')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.original_source_urls.map((source, index) => (
                                    <li key={index} className="flex items-center gap-2 text-sm">
                                        <Badge variant="outline" className="text-xs">
                                            {source.type || t('recipe.source')}
                                        </Badge>
                                        {source.url && source.url !== 'unknown' ? (
                                            <a href={source.url} target="_blank" rel="noopener noreferrer" 
                                               className="text-[#6A1F2E] hover:underline truncate">
                                                {source.url}
                                            </a>
                                        ) : (
                                            <span className="text-[#1E1E1E]/50">{t('recipe.source')}</span>
                                        )}
                                        {source.language && (
                                            <span className="text-xs text-[#1E1E1E]/50 uppercase">({source.language})</span>
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
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <Youtube className="h-5 w-5 text-red-600" />
                                {t('recipe.videoTutorials')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.youtube_links.filter(link => link.url).map((link, index) => (
                                    <li key={index}>
                                        <a href={link.url} target="_blank" rel="noopener noreferrer"
                                           className="text-[#6A1F2E] hover:underline flex items-center gap-2">
                                            <Youtube className="h-4 w-4" />
                                            {link.title || t('recipe.watchVideo')}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                )}

                {/* Ratings & Reviews Section */}
                <ReviewSection 
                    slug={slug} 
                    initialRating={recipe.average_rating || 0}
                    initialCount={recipe.ratings_count || 0}
                />

                {/* Metadata */}
                <div className="text-center text-sm text-[#1E1E1E]/50 pt-8 border-t">
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
