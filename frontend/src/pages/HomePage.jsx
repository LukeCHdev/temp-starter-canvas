import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { 
    Globe, ArrowRight, CheckCircle2, Users, BookOpen, Utensils, ChefHat
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
    { key: 'Europe', slug: 'europe', emoji: '🇪🇺', accent: 'border-l-burgundy' },
    { key: 'Asia', slug: 'asia', emoji: '🌏', accent: 'border-l-gold' },
    { key: 'Americas', slug: 'americas', emoji: '🌎', accent: 'border-l-secondary' },
    { key: 'Africa', slug: 'africa', emoji: '🌍', accent: 'border-l-accent' },
    { key: 'Middle East', slug: 'middle-east', emoji: '🕌', accent: 'border-l-primary' },
    { key: 'Oceania', slug: 'oceania', emoji: '🏝️', accent: 'border-l-olive' },
];

const HomePage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const lang = language || 'en';
    
    const [featuredRecipe, setFeaturedRecipe] = useState(null);
    const [curatedRecipes, setCuratedRecipes] = useState([]);
    const [loading, setLoading] = useState(true);

    const getAuthenticityLabel = (level) => {
        switch(level) {
            case 1: return t('badges.officiallyRecognized', lang);
            case 2: return t('badges.traditionVerified', lang);
            case 3: return t('badges.traditional', lang);
            default: return t('badges.traditional', lang);
        }
    };

    const loadData = useCallback(async () => {
        try {
            const [bestRes, featuredRes] = await Promise.all([
                recipeAPI.getBest(lang),
                recipeAPI.getFeatured(6, lang)
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

    return (
        <div className="min-h-screen bg-background" data-testid="homepage">
            
            {/* ═══ DRAMATIC HERO ═══ */}
            <section 
                className="relative overflow-hidden py-20 sm:py-28 lg:py-36 px-4"
                style={{ background: 'var(--gradient-hero)' }}
            >
                {/* Subtle texture overlay */}
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'1\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")' }} />
                
                <div className="relative max-w-3xl mx-auto text-center">
                    {/* Gold accent line */}
                    <div className="w-12 h-px mx-auto mb-8" style={{ background: 'var(--gradient-gold)' }} />
                    
                    <h1 className="text-4xl sm:text-5xl lg:text-7xl font-light text-primary-foreground mb-5 sm:mb-6 tracking-tight fade-in-up leading-[1.1]" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.hero.title', lang)}
                    </h1>
                    <p className="text-base sm:text-lg text-primary-foreground/70 mb-10 sm:mb-12 font-light fade-in-up fade-in-up-delay-1 max-w-xl mx-auto">
                        {t('homepage.hero.subtitle', lang)}
                    </p>
                    
                    <div className="relative max-w-2xl mx-auto fade-in-up fade-in-up-delay-2">
                        <SearchBar className="w-full" />
                        <p className="text-xs text-primary-foreground/50 mt-3 font-light">
                            {t('homepage.hero.searchHelper', lang)}
                        </p>
                    </div>
                </div>
            </section>

            {/* ═══ VALUE STRIP ═══ */}
            <section className="bg-card border-b border-border py-5 sm:py-6 -mt-px">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-center gap-6 sm:gap-10 text-xs sm:text-sm text-muted-foreground flex-wrap">
                        <span className="flex items-center gap-2 fade-in-up fade-in-up-delay-1">
                            <Globe className="h-4 w-4 text-primary" />
                            {t('homepage.valueStrip.curated', lang)}
                        </span>
                        <span className="flex items-center gap-2 fade-in-up fade-in-up-delay-2">
                            <Users className="h-4 w-4 text-primary" />
                            {t('homepage.valueStrip.validated', lang)}
                        </span>
                        <span className="flex items-center gap-2 fade-in-up fade-in-up-delay-3">
                            <CheckCircle2 className="h-4 w-4 text-primary" />
                            {t('homepage.valueStrip.accuracy', lang)}
                        </span>
                    </div>
                </div>
            </section>

            {/* ═══ FEATURED RECIPE HERO ═══ */}
            {featuredRecipe && !loading && (
                <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
                    <Link to={getLocalizedPath(`/recipe/${featuredRecipe.slug}`)} className="block group">
                        <div className="bg-card border border-border overflow-hidden recipe-card-hover" style={{ boxShadow: 'var(--shadow-card)' }} data-testid="featured-recipe-hero">
                            <div className="grid md:grid-cols-2">
                                <div className="relative h-56 sm:h-72 md:h-[400px] bg-muted overflow-hidden">
                                    {featuredRecipe.photos && featuredRecipe.photos[0]?.image_url ? (
                                        <img 
                                            src={featuredRecipe.photos[0].image_url} 
                                            alt={featuredRecipe.recipe_name}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center bg-muted">
                                            <ChefHat className="h-16 w-16 text-accent/30" />
                                        </div>
                                    )}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                </div>

                                <div className="p-6 sm:p-8 md:p-10 flex flex-col justify-center bg-card">
                                    <div className="mb-4">
                                        <span className="inline-block text-[10px] sm:text-xs uppercase tracking-widest text-primary font-medium border border-primary px-3 py-1">
                                            {getAuthenticityLabel(featuredRecipe.authenticity_level)}
                                        </span>
                                    </div>

                                    <div className="text-xs sm:text-sm text-muted-foreground mb-3 tracking-wide">
                                        {t(`countries.${featuredRecipe.origin_country || featuredRecipe.country}`, lang)}
                                        {(featuredRecipe.origin_region || featuredRecipe.region) && (
                                            <span> · {featuredRecipe.origin_region || featuredRecipe.region}</span>
                                        )}
                                    </div>

                                    <h2 className="text-xl sm:text-2xl md:text-3xl font-light text-foreground mb-4 leading-tight" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {featuredRecipe.recipe_name || featuredRecipe.title_original}
                                    </h2>

                                    <p className="text-muted-foreground mb-6 leading-relaxed line-clamp-3 font-light text-xs sm:text-sm">
                                        {featuredRecipe.characteristic_profile || featuredRecipe.history_summary || featuredRecipe.origin_story}
                                    </p>

                                    <div className="flex items-center text-primary font-medium group-hover:gap-3 transition-all text-xs sm:text-sm">
                                        <span>{t('homepage.hero.exploreRecipe', lang)}</span>
                                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Link>
                </section>
            )}

            {/* ═══ HOW AUTHENTICITY WORKS ═══ */}
            <section className="bg-card py-14 sm:py-20 border-t border-b border-border">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-2xl sm:text-3xl font-light text-center text-foreground mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.authenticity.title', lang)}
                    </h2>
                    <div className="section-divider mb-10 sm:mb-12"></div>

                    <div className="grid md:grid-cols-3 gap-10 sm:gap-12">
                        {[
                            { num: '1', titleKey: 'step1Title', textKey: 'step1Text', icon: BookOpen },
                            { num: '2', titleKey: 'step2Title', textKey: 'step2Text', icon: Users },
                            { num: '3', titleKey: 'step3Title', textKey: 'step3Text', icon: CheckCircle2 },
                        ].map((step, i) => (
                            <div key={step.num} className={`text-center fade-in-up fade-in-up-delay-${i + 1}`}>
                                <div className="w-14 h-14 rounded-full border-2 border-primary flex items-center justify-center mx-auto mb-5 bg-primary/5">
                                    <step.icon className="h-5 w-5 text-primary" />
                                </div>
                                <h3 className="text-lg font-medium text-foreground mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`homepage.authenticity.${step.titleKey}`, lang)}
                                </h3>
                                <p className="text-sm text-muted-foreground leading-relaxed font-light">
                                    {t(`homepage.authenticity.${step.textKey}`, lang)}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ═══ BROWSE BY CONTINENT ═══ */}
            <section className="bg-background py-14 sm:py-20">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10 sm:mb-12">
                        <h2 className="text-2xl sm:text-3xl font-light text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.browseContinent.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {/* Desktop grid */}
                    <div className="hidden sm:grid grid-cols-2 md:grid-cols-3 gap-4">
                        {CONTINENT_KEYS.map((continent, i) => (
                            <Link 
                                key={continent.slug}
                                to={getLocalizedPath(`/explore/${continent.slug}`)}
                                className={`group flex items-center gap-4 p-5 sm:p-6 bg-card border border-border ${continent.accent} border-l-4 hover:border-l-primary hover:shadow-md transition-all duration-300 recipe-card-hover fade-in-up fade-in-up-delay-${Math.min(i + 1, 5)}`}
                                data-testid={`continent-${continent.slug}`}
                            >
                                <span className="text-2xl sm:text-3xl">{continent.emoji}</span>
                                <div>
                                    <h3 className="text-base sm:text-lg font-light text-foreground group-hover:text-primary transition-colors" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {t(`continents.${continent.key}`, lang)}
                                    </h3>
                                </div>
                                <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
                            </Link>
                        ))}
                    </div>
                    {/* Mobile: horizontal scroll */}
                    <div className="sm:hidden scroll-container -mx-4 px-4">
                        {CONTINENT_KEYS.map((continent) => (
                            <Link 
                                key={continent.slug}
                                to={getLocalizedPath(`/explore/${continent.slug}`)}
                                className="group flex items-center gap-3 min-w-[180px] p-5 bg-card border border-border border-l-4 border-l-primary hover:shadow-md transition-all duration-300 flex-shrink-0"
                                data-testid={`continent-mobile-${continent.slug}`}
                            >
                                <span className="text-2xl">{continent.emoji}</span>
                                <h3 className="text-base font-light text-foreground group-hover:text-primary transition-colors whitespace-nowrap" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`continents.${continent.key}`, lang)}
                                </h3>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* ═══ BROWSE BY DISH TYPE ═══ */}
            <section className="bg-card py-14 sm:py-20 border-t border-border">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10 sm:mb-12">
                        <h2 className="text-2xl sm:text-3xl font-light text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.browseDishType.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {/* Desktop grid */}
                    <div className="hidden sm:grid grid-cols-2 md:grid-cols-4 gap-4">
                        {DISH_TYPE_KEYS.map((type) => (
                            <Link 
                                key={type.key}
                                to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                className="group flex flex-col items-center gap-2 p-5 text-center border border-border bg-background hover:border-primary hover:bg-card transition-all duration-300 recipe-card-hover"
                                data-testid={`dish-type-${type.slug}`}
                            >
                                <span className="text-2xl mb-1">{type.icon}</span>
                                <span className="text-foreground group-hover:text-primary transition-colors font-light text-sm" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`homepage.dishTypes.${type.key}`, lang)}
                                </span>
                            </Link>
                        ))}
                    </div>
                    {/* Mobile: horizontal scroll */}
                    <div className="sm:hidden scroll-container -mx-4 px-4">
                        {DISH_TYPE_KEYS.map((type) => (
                            <Link 
                                key={type.key}
                                to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                className="group flex flex-col items-center gap-2 min-w-[120px] p-4 text-center border border-border bg-background hover:border-primary transition-all duration-300 flex-shrink-0"
                                data-testid={`dish-type-mobile-${type.slug}`}
                            >
                                <span className="text-xl">{type.icon}</span>
                                <span className="text-foreground group-hover:text-primary transition-colors font-light text-sm whitespace-nowrap" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`homepage.dishTypes.${type.key}`, lang)}
                                </span>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* ═══ CURATED RECIPES ═══ */}
            <section className="bg-background py-14 sm:py-20 border-t border-border">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10 sm:mb-12">
                        <h2 className="text-2xl sm:text-3xl font-light text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.curatedRecipes.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {loading ? (
                        <div className="text-center py-16" data-testid="loading-state">
                            <div className="w-12 h-12 rounded-full border-2 border-primary/20 border-t-primary animate-spin mx-auto mb-4" />
                            <p className="text-muted-foreground font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                        </div>
                    ) : curatedRecipes.length > 0 ? (
                        <>
                            <div className="hidden sm:grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="curated-recipes-grid">
                                {curatedRecipes.slice(0, 6).map((recipe) => (
                                    <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                                ))}
                            </div>
                            <div className="sm:hidden scroll-container -mx-4 px-4" data-testid="curated-recipes-scroll">
                                {curatedRecipes.slice(0, 6).map((recipe) => (
                                    <div key={recipe.slug} className="min-w-[280px] max-w-[300px] flex-shrink-0">
                                        <RecipeCard recipe={recipe} variant="editorial" />
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        /* Graceful fallback when no API data */
                        <div className="text-center py-16" data-testid="no-recipes-state">
                            <Utensils className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                            <p className="text-muted-foreground font-light mb-6 text-lg" style={{ fontFamily: 'var(--font-heading)' }}>
                                {t('homepage.curatedRecipes.emptyTitle', lang)}
                            </p>
                            <Link to={getLocalizedPath('/explore')}>
                                <Button variant="outline" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground rounded-none px-8 font-light tracking-wide text-sm">
                                    {t('homepage.curatedRecipes.browseCollection', lang)}
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </div>
                    )}

                    {curatedRecipes.length > 0 && (
                        <div className="text-center mt-10 sm:mt-12">
                            <Link to={getLocalizedPath('/explore')}>
                                <Button 
                                    variant="outline" 
                                    className="border-primary text-primary hover:bg-primary hover:text-primary-foreground px-10 py-2.5 rounded-none font-light tracking-wide text-sm transition-all duration-300"
                                    data-testid="explore-all-btn"
                                >
                                    {t('homepage.curatedRecipes.exploreAll', lang)}
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </div>
                    )}
                </div>
            </section>

            {/* ═══ FOOTER CTA ═══ */}
            <section className="py-14 sm:py-16" style={{ background: 'var(--gradient-hero)' }}>
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <div className="w-10 h-px mx-auto mb-6" style={{ background: 'var(--gradient-gold)' }} />
                    <p className="text-primary-foreground/80 mb-6 sm:mb-8 font-light text-sm sm:text-base" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.footer.tagline', lang)}
                    </p>
                    <Link to={getLocalizedPath('/editorial-policy')}>
                        <Button 
                            variant="outline" 
                            className="border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground hover:text-foreground rounded-none px-10 font-light tracking-wide text-sm transition-all duration-300"
                        >
                            {t('homepage.footer.editorialStandards', lang)}
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
