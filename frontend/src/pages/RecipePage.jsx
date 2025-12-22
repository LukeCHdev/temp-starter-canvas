import React, { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI } from '@/utils/api';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { RecipeSEO } from '@/components/seo/SEOHelmet';
import { useLanguage } from '@/context/LanguageContext';
import { ReviewSection } from '@/components/recipe/ReviewSection';
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

const RecipePage = () => {
    const { slug } = useParams();
    const [recipe, setRecipe] = useState(null);
    const [loading, setLoading] = useState(true);
    const { language } = useLanguage();
    const { t } = useTranslation();

    // Memoize language to prevent unnecessary re-fetches
    const currentLang = useMemo(() => language?.split('-')[0] || 'en', [language]);

    useEffect(() => {
        let isMounted = true;
        
        const loadRecipe = async () => {
            setLoading(true);
            try {
                const res = await recipeAPI.getBySlug(slug, currentLang);
                if (isMounted) {
                    setRecipe(res.data);
                }
            } catch (error) {
                if (isMounted) {
                    toast.error(t('recipe.notFound'));
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        loadRecipe();
        
        return () => {
            isMounted = false;
        };
    }, [slug, currentLang, t]);

    // Memoized authenticity helpers
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

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center" data-testid="loading-state">
                <div className="text-center">
                    <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                    <p className="text-[#1E1E1E]/70">{t('recipe.loadingRecipe')}</p>
                </div>
            </div>
        );
    }

    if (!recipe) {
        return (
            <div className="min-h-screen flex items-center justify-center" data-testid="not-found-state">
                <div className="text-center">
                    <p className="text-xl text-[#1E1E1E]/70 mb-4">{t('recipe.notFound')}</p>
                    <Link to="/" className="text-[#6A1F2E] hover:underline">
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

    return (
        <div className="min-h-screen" data-testid="recipe-page">
            {/* SEO Metadata */}
            <RecipeSEO recipe={recipe} url={window.location.href} />
            
            {/* Hero Section */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto">
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
                {(recipe.history_summary || recipe.origin_story) && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <BookOpen className="h-5 w-5 text-[#6A1F2E]" />
                                {t('recipe.history')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed">
                                {recipe.history_summary || recipe.origin_story}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {recipe.characteristic_profile && (
                    <Card className="card-elegant">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <ChefHat className="h-5 w-5 text-[#3F4A3C]" />
                                {t('recipe.profile')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="narrative-text leading-relaxed">
                                {recipe.characteristic_profile}
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* No-No Rules */}
                {recipe.no_no_rules && recipe.no_no_rules.length > 0 && (
                    <Card className="card-elegant border-l-4 border-l-red-500">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-red-700" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                <AlertTriangle className="h-5 w-5" />
                                {t('recipe.noNoRules')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                {recipe.no_no_rules.map((rule, index) => (
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
