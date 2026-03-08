import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { 
    Globe, ArrowRight, CheckCircle2, Users, BookOpen, Utensils, ChefHat, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const DISH_TYPE_KEYS = [
    { key: 'appetizer', slug: 'appetizer', icon: '🥗' },
    { key: 'aperitif', slug: 'aperitif', icon: '🍷' },
    { key: 'firstCourse', slug: 'first-course', icon: '🍝' },
    { key: 'mainCourse', slug: 'main-course', icon: '🥘' },
    { key: 'sideDish', slug: 'side-dish', icon: '🥬' },
    { key: 'dessert', slug: 'dessert', icon: '🍰' },
    { key: 'streetFood', slug: 'street-food', icon: '🌮' },
    { key: 'festive', slug: 'festive', icon: '🎉' },
];

const CONTINENT_KEYS = [
    { key: 'Europe', slug: 'europe', emoji: '🇪🇺' },
    { key: 'Asia', slug: 'asia', emoji: '🌏' },
    { key: 'Americas', slug: 'americas', emoji: '🌎' },
    { key: 'Africa', slug: 'africa', emoji: '🌍' },
    { key: 'Middle East', slug: 'middle-east', emoji: '🕌' },
    { key: 'Oceania', slug: 'oceania', emoji: '🏝️' },
];

const HomePage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    
    const [featuredRecipe, setFeaturedRecipe] = useState(null);
    const [curatedRecipes, setCuratedRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [heroIndex, setHeroIndex] = useState(0);

    const loadData = useCallback(async () => {
        try {
            const [bestRes, featuredRes] = await Promise.all([
                recipeAPI.getBest(lang),
                recipeAPI.getFeatured(12, lang)
            ]);
            
            setFeaturedRecipe(bestRes.data.recipe);
            setCuratedRecipes(featuredRes.data.recipes || []);
        } catch (error) {
            console.error('Error loading data:', error);
        } finally {
            setLoading(false);
        }
    }, [lang]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Hero carousel auto-advance
    const heroSlides = curatedRecipes.slice(0, 4);
    useEffect(() => {
        if (heroSlides.length <= 1) return;
        const timer = setInterval(() => setHeroIndex((c) => (c + 1) % heroSlides.length), 5000);
        return () => clearInterval(timer);
    }, [heroSlides.length]);

    const getHeroImage = (recipe) => {
        const photos = recipe?.metadata?.photos || recipe?.photos;
        return (photos && photos[0]?.image_url) || recipe?.image_url || null;
    };

    const getHeroTitle = (recipe) => {
        const translations = recipe?.translations || {};
        const langT = translations[lang] || {};
        if (langT.status === 'ready' && (langT.recipe_name || langT.title)) {
            return langT.recipe_name || langT.title;
        }
        return recipe?.recipe_name || recipe?.title_original || '';
    };

    // Split curated recipes into sections for horizontal scroll
    const section1 = curatedRecipes.slice(0, 6);
    const section2 = curatedRecipes.slice(6, 12);

    return (
        <div className="min-h-screen bg-background" data-testid="homepage">
            
            {/* ═══ HERO CAROUSEL (Elegant Sona style) ═══ */}
            <section className="relative h-[85vh] overflow-hidden mt-20">
                {heroSlides.length > 0 ? heroSlides.map((recipe, i) => (
                    <div
                        key={recipe.slug || i}
                        className="absolute inset-0 transition-opacity duration-1000 ease-in-out"
                        style={{ opacity: heroIndex === i ? 1 : 0 }}
                    >
                        {getHeroImage(recipe) ? (
                            <img
                                src={getHeroImage(recipe)}
                                alt={getHeroTitle(recipe)}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <div className="w-full h-full bg-muted flex items-center justify-center">
                                <ChefHat className="h-24 w-24 text-muted-foreground/20" />
                            </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
                    </div>
                )) : (
                    <div className="absolute inset-0 bg-muted flex items-center justify-center">
                        <ChefHat className="h-24 w-24 text-muted-foreground/20" />
                        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
                    </div>
                )}

                {/* Hero text overlay */}
                <div className="absolute bottom-20 left-0 right-0 text-center z-10">
                    <h1 className="text-5xl md:text-7xl font-light tracking-wider text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {heroSlides.length > 0 
                            ? getHeroTitle(heroSlides[heroIndex]) 
                            : t('homepage.hero.title', lang)
                        }
                    </h1>
                    <Link
                        to={heroSlides.length > 0 
                            ? getLocalizedPath(`/recipe/${heroSlides[heroIndex]?.slug}`)
                            : getLocalizedPath('/explore')
                        }
                        className="inline-block text-sm font-medium tracking-widest uppercase text-primary border-b border-primary pb-1 hover:opacity-80 transition-opacity"
                        style={{ fontFamily: 'var(--font-body)' }}
                    >
                        {t('homepage.hero.exploreRecipe', lang)}
                    </Link>
                </div>

                {/* Carousel dots */}
                {heroSlides.length > 1 && (
                    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-2 z-10">
                        {heroSlides.map((_, i) => (
                            <button
                                key={i}
                                onClick={() => setHeroIndex(i)}
                                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                                    heroIndex === i ? 'bg-primary w-6' : 'bg-muted-foreground/40'
                                }`}
                                aria-label={`Slide ${i + 1}`}
                            />
                        ))}
                    </div>
                )}

                {/* Search bar overlay */}
                <div className="absolute top-8 left-1/2 -translate-x-1/2 w-full max-w-xl px-6 z-10">
                    <SearchBar className="w-full" />
                </div>
            </section>

            {/* ═══ RECIPE SECTION 1: Horizontal Scroll ═══ */}
            <div className="py-8">
                {section1.length > 0 && (
                    <section className="py-16 px-6">
                        <div className="container mx-auto">
                            <div className="flex items-end justify-between mb-10">
                                <div>
                                    <h2 className="text-4xl md:text-5xl font-light tracking-wide text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t('homepage.curatedRecipes.title', lang)}
                                    </h2>
                                    <div className="w-12 h-px bg-primary mt-4" />
                                </div>
                                <Link
                                    to={getLocalizedPath('/explore')}
                                    className="hidden md:flex items-center gap-1 text-sm font-medium text-primary hover:opacity-80 transition-opacity tracking-wide"
                                    style={{ fontFamily: 'var(--font-body)' }}
                                >
                                    {t('homepage.curatedRecipes.exploreAll', lang)}
                                    <ChevronRight className="w-4 h-4" />
                                </Link>
                            </div>

                            <div className="scroll-container">
                                {section1.map((recipe) => (
                                    <RecipeCard key={recipe.slug} recipe={recipe} variant="scroll" />
                                ))}
                            </div>

                            <Link
                                to={getLocalizedPath('/explore')}
                                className="md:hidden flex items-center gap-1 text-sm font-medium text-primary mt-6 tracking-wide"
                                style={{ fontFamily: 'var(--font-body)' }}
                            >
                                {t('homepage.curatedRecipes.exploreAll', lang)}
                                <ChevronRight className="w-4 h-4" />
                            </Link>
                        </div>
                    </section>
                )}

                <div className="section-divider" />

                {/* ═══ BROWSE BY CONTINENT ═══ */}
                <section className="py-16 px-6">
                    <div className="container mx-auto">
                        <div className="flex items-end justify-between mb-10">
                            <div>
                                <h2 className="text-4xl md:text-5xl font-light tracking-wide text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t('homepage.browseContinent.title', lang)}
                                </h2>
                                <div className="w-12 h-px bg-primary mt-4" />
                            </div>
                        </div>

                        <div className="scroll-container">
                            {CONTINENT_KEYS.map((continent) => (
                                <Link
                                    key={continent.slug}
                                    to={getLocalizedPath(`/explore/${continent.slug}`)}
                                    className="recipe-card-hover group flex-shrink-0 w-48 block text-center"
                                    data-testid={`continent-${continent.slug}`}
                                >
                                    <div className="w-full aspect-square bg-card border border-border rounded-sm flex items-center justify-center group-hover:border-primary transition-colors duration-300">
                                        <span className="text-5xl">{continent.emoji}</span>
                                    </div>
                                    <h3 className="text-xl font-medium mt-4 text-foreground group-hover:text-primary transition-colors duration-300" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t(`continents.${continent.key}`, lang)}
                                    </h3>
                                </Link>
                            ))}
                        </div>
                    </div>
                </section>

                <div className="section-divider" />

                {/* ═══ RECIPE SECTION 2 ═══ */}
                {section2.length > 0 && (
                    <>
                        <section className="py-16 px-6">
                            <div className="container mx-auto">
                                <div className="flex items-end justify-between mb-10">
                                    <div>
                                        <h2 className="text-4xl md:text-5xl font-light tracking-wide text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                                            {t('homepage.browseDishType.title', lang)}
                                        </h2>
                                        <div className="w-12 h-px bg-primary mt-4" />
                                    </div>
                                </div>

                                <div className="scroll-container">
                                    {section2.map((recipe) => (
                                        <RecipeCard key={recipe.slug} recipe={recipe} variant="scroll" />
                                    ))}
                                </div>
                            </div>
                        </section>

                        <div className="section-divider" />
                    </>
                )}

                {/* ═══ BROWSE BY DISH TYPE ═══ */}
                <section className="py-16 px-6">
                    <div className="container mx-auto">
                        <div className="flex items-end justify-between mb-10">
                            <div>
                                <h2 className="text-4xl md:text-5xl font-light tracking-wide text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t('homepage.browseDishType.title', lang)}
                                </h2>
                                <div className="w-12 h-px bg-primary mt-4" />
                            </div>
                        </div>

                        <div className="scroll-container">
                            {DISH_TYPE_KEYS.map((type) => (
                                <Link
                                    key={type.key}
                                    to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                    className="recipe-card-hover group flex-shrink-0 w-40 block text-center"
                                    data-testid={`dish-type-${type.slug}`}
                                >
                                    <div className="w-full aspect-square bg-card border border-border rounded-sm flex items-center justify-center group-hover:border-primary transition-colors duration-300">
                                        <span className="text-4xl">{type.icon}</span>
                                    </div>
                                    <h3 className="text-lg font-medium mt-3 text-foreground group-hover:text-primary transition-colors duration-300" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t(`homepage.dishTypes.${type.key}`, lang)}
                                    </h3>
                                </Link>
                            ))}
                        </div>
                    </div>
                </section>

                {loading && (
                    <div className="text-center py-16" data-testid="loading-state">
                        <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin mx-auto mb-4" />
                        <p className="text-muted-foreground font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default HomePage;
