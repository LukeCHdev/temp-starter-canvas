import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI, continentAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n/translations';
import { 
    Globe, ArrowRight, CheckCircle2, Users
} from 'lucide-react';
import { toast } from 'sonner';

const DISH_TYPE_KEYS = [
    { key: 'appetizer', slug: 'appetizer' },
    { key: 'aperitif', slug: 'aperitif' },
    { key: 'firstCourse', slug: 'first-course' },
    { key: 'mainCourse', slug: 'main-course' },
    { key: 'sideDish', slug: 'side-dish' },
    { key: 'dessert', slug: 'dessert' },
    { key: 'streetFood', slug: 'street-food' },
    { key: 'festive', slug: 'festive' },
];

const CONTINENT_KEYS = [
    { key: 'Europe', slug: 'europe' },
    { key: 'Asia', slug: 'asia' },
    { key: 'Americas', slug: 'americas' },
    { key: 'Africa', slug: 'africa' },
    { key: 'Middle East', slug: 'middle-east' },
    { key: 'Oceania', slug: 'oceania' },
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
            toast.error(t('search.failed', lang));
        } finally {
            setLoading(false);
        }
    }, [lang]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    return (
        <div className="min-h-screen bg-[#FDFBF7]" data-testid="homepage">
            
            {/* VALUE STRIP */}
            <section className="bg-[#FDFBF7] border-b border-[#E8E4DC] py-5 sm:py-6">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-[#2C2C2C] text-base sm:text-lg font-light tracking-wide" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.valueStrip.main', lang)}
                    </p>
                    <div className="flex justify-center gap-4 sm:gap-8 mt-3 sm:mt-4 text-xs sm:text-sm text-[#5C5C5C] flex-wrap">
                        <span className="flex items-center gap-1.5 sm:gap-2 fade-in-up fade-in-up-delay-1">
                            <Globe className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.curated', lang)}
                        </span>
                        <span className="flex items-center gap-1.5 sm:gap-2 fade-in-up fade-in-up-delay-2">
                            <Users className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.validated', lang)}
                        </span>
                        <span className="flex items-center gap-1.5 sm:gap-2 fade-in-up fade-in-up-delay-3">
                            <CheckCircle2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.accuracy', lang)}
                        </span>
                    </div>
                </div>
            </section>

            {/* HERO SEARCH */}
            <section className="bg-[#FDFBF7] py-12 sm:py-16 lg:py-20 px-4">
                <div className="max-w-3xl mx-auto text-center">
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-light text-[#2C2C2C] mb-4 sm:mb-6 tracking-tight fade-in-up" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.hero.title', lang)}
                    </h1>
                    <p className="text-base sm:text-lg text-[#5C5C5C] mb-8 sm:mb-10 font-light fade-in-up fade-in-up-delay-1">
                        {t('homepage.hero.subtitle', lang)}
                    </p>
                    
                    <div className="relative max-w-2xl mx-auto fade-in-up fade-in-up-delay-2">
                        <SearchBar className="w-full" />
                        <p className="text-xs text-[#7C7C7C] mt-3 font-light">
                            {t('homepage.hero.searchHelper', lang)}
                        </p>
                    </div>
                </div>
            </section>

            {/* FEATURED RECIPE HERO */}
            {featuredRecipe && !loading && (
                <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
                    <Link to={getLocalizedPath(`/recipe/${featuredRecipe.slug}`)} className="block group">
                        <div className="bg-white border border-[#E8E4DC] overflow-hidden recipe-card-hover" data-testid="featured-recipe-hero">
                            <div className="grid md:grid-cols-2">
                                <div className="relative h-56 sm:h-72 md:h-[380px] bg-[#F5F2EC] overflow-hidden">
                                    {featuredRecipe.photos && featuredRecipe.photos[0]?.image_url ? (
                                        <img 
                                            src={featuredRecipe.photos[0].image_url} 
                                            alt={featuredRecipe.recipe_name}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <span className="text-[#BFBFBF] text-5xl sm:text-6xl font-light" style={{ fontFamily: 'var(--font-heading)' }}>SCL</span>
                                        </div>
                                    )}
                                    {/* Gradient overlay */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                </div>

                                <div className="p-6 sm:p-8 md:p-10 flex flex-col justify-center bg-white">
                                    <div className="mb-3 sm:mb-4">
                                        <span className="inline-block text-[10px] sm:text-xs uppercase tracking-widest text-[#6A1F2E] font-medium border border-[#6A1F2E] px-2.5 sm:px-3 py-0.5 sm:py-1">
                                            {getAuthenticityLabel(featuredRecipe.authenticity_level)}
                                        </span>
                                    </div>

                                    <div className="text-xs sm:text-sm text-[#7C7C7C] mb-2 sm:mb-3 tracking-wide">
                                        {t(`countries.${featuredRecipe.origin_country || featuredRecipe.country}`, lang)}
                                        {(featuredRecipe.origin_region || featuredRecipe.region) && (
                                            <span> · {featuredRecipe.origin_region || featuredRecipe.region}</span>
                                        )}
                                    </div>

                                    <h2 className="text-xl sm:text-2xl md:text-3xl font-light text-[#2C2C2C] mb-3 sm:mb-4 leading-tight" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {featuredRecipe.recipe_name || featuredRecipe.title_original}
                                    </h2>

                                    <p className="text-[#5C5C5C] mb-4 sm:mb-6 leading-relaxed line-clamp-3 font-light text-xs sm:text-sm">
                                        {featuredRecipe.characteristic_profile || featuredRecipe.history_summary || featuredRecipe.origin_story}
                                    </p>

                                    <div className="flex items-center text-[#6A1F2E] font-medium group-hover:gap-3 transition-all text-xs sm:text-sm">
                                        <span>{t('homepage.hero.exploreRecipe', lang)}</span>
                                        <ArrowRight className="ml-2 h-3.5 w-3.5 sm:h-4 sm:w-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Link>
                </section>
            )}

            {/* HOW AUTHENTICITY WORKS */}
            <section className="bg-white py-12 sm:py-16 border-t border-b border-[#E8E4DC]">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-xl sm:text-2xl font-light text-center text-[#2C2C2C] mb-3 sm:mb-4" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.authenticity.title', lang)}
                    </h2>
                    <div className="section-divider mb-8 sm:mb-10"></div>

                    <div className="grid md:grid-cols-3 gap-8 sm:gap-10">
                        {[
                            { num: '1', titleKey: 'step1Title', textKey: 'step1Text' },
                            { num: '2', titleKey: 'step2Title', textKey: 'step2Text' },
                            { num: '3', titleKey: 'step3Title', textKey: 'step3Text' },
                        ].map((step, i) => (
                            <div key={step.num} className={`text-center fade-in-up fade-in-up-delay-${i + 1}`}>
                                <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                    <span className="text-[#6A1F2E] font-medium text-sm">{step.num}</span>
                                </div>
                                <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`homepage.authenticity.${step.titleKey}`, lang)}
                                </h3>
                                <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                    {t(`homepage.authenticity.${step.textKey}`, lang)}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* BROWSE BY CONTINENT */}
            <section className="bg-[#FDFBF7] py-12 sm:py-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-8 sm:mb-10">
                        <h2 className="text-xl sm:text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.browseContinent.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {/* Desktop: grid, Mobile: horizontal scroll */}
                    <div className="hidden sm:grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {CONTINENT_KEYS.map((continent, i) => (
                            <Link 
                                key={continent.slug}
                                to={getLocalizedPath(`/explore/${continent.slug}`)}
                                className={`group block p-5 sm:p-6 bg-white border border-[#E8E4DC] hover:border-[#6A1F2E] transition-all duration-300 text-center recipe-card-hover fade-in-up fade-in-up-delay-${Math.min(i + 1, 5)}`}
                                data-testid={`continent-${continent.slug}`}
                            >
                                <h3 className="text-base sm:text-lg font-light text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`continents.${continent.key}`, lang)}
                                </h3>
                            </Link>
                        ))}
                    </div>
                    {/* Mobile: horizontal scroll container */}
                    <div className="sm:hidden scroll-container -mx-4 px-4">
                        {CONTINENT_KEYS.map((continent) => (
                            <Link 
                                key={continent.slug}
                                to={getLocalizedPath(`/explore/${continent.slug}`)}
                                className="group block min-w-[140px] p-5 bg-white border border-[#E8E4DC] hover:border-[#6A1F2E] transition-all duration-300 text-center flex-shrink-0"
                                data-testid={`continent-mobile-${continent.slug}`}
                            >
                                <h3 className="text-base font-light text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors whitespace-nowrap" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`continents.${continent.key}`, lang)}
                                </h3>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* BROWSE BY DISH TYPE */}
            <section className="bg-white py-12 sm:py-16 border-t border-[#E8E4DC]">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-8 sm:mb-10">
                        <h2 className="text-xl sm:text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.browseDishType.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {/* Desktop: grid, Mobile: horizontal scroll */}
                    <div className="hidden sm:grid grid-cols-2 md:grid-cols-4 gap-3">
                        {DISH_TYPE_KEYS.map((type) => (
                            <Link 
                                key={type.key}
                                to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                className="group block p-4 text-center border border-[#E8E4DC] bg-[#FDFBF7] hover:border-[#6A1F2E] hover:bg-white transition-all duration-300"
                                data-testid={`dish-type-${type.slug}`}
                            >
                                <span className="text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors font-light text-sm" style={{ fontFamily: 'var(--font-heading)' }}>
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
                                className="group block min-w-[120px] p-4 text-center border border-[#E8E4DC] bg-[#FDFBF7] hover:border-[#6A1F2E] hover:bg-white transition-all duration-300 flex-shrink-0"
                                data-testid={`dish-type-mobile-${type.slug}`}
                            >
                                <span className="text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors font-light text-sm whitespace-nowrap" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {t(`homepage.dishTypes.${type.key}`, lang)}
                                </span>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* CURATED RECIPES */}
            <section className="bg-[#FDFBF7] py-12 sm:py-16 border-t border-[#E8E4DC]">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-8 sm:mb-10">
                        <h2 className="text-xl sm:text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {t('homepage.curatedRecipes.title', lang)}
                        </h2>
                        <div className="section-divider"></div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12" data-testid="loading-state">
                            <p className="text-[#7C7C7C] font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                        </div>
                    ) : curatedRecipes.length > 0 ? (
                        <>
                            {/* Desktop: grid */}
                            <div className="hidden sm:grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="curated-recipes-grid">
                                {curatedRecipes.slice(0, 6).map((recipe) => (
                                    <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                                ))}
                            </div>
                            {/* Mobile: horizontal scroll */}
                            <div className="sm:hidden scroll-container -mx-4 px-4" data-testid="curated-recipes-scroll">
                                {curatedRecipes.slice(0, 6).map((recipe) => (
                                    <div key={recipe.slug} className="min-w-[280px] max-w-[300px] flex-shrink-0">
                                        <RecipeCard recipe={recipe} variant="editorial" />
                                    </div>
                                ))}
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-12" data-testid="no-recipes-state">
                            <p className="text-[#7C7C7C] font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                        </div>
                    )}

                    <div className="text-center mt-8 sm:mt-10">
                        <Link to={getLocalizedPath('/explore')}>
                            <Button 
                                variant="outline" 
                                className="border-[#6A1F2E] text-[#6A1F2E] hover:bg-[#6A1F2E] hover:text-white px-8 py-2 rounded-none font-light tracking-wide text-sm transition-all duration-300"
                                data-testid="explore-all-btn"
                            >
                                {t('homepage.curatedRecipes.exploreAll', lang)}
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* FOOTER CTA */}
            <section className="bg-[#2C2C2C] py-12 sm:py-14">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <p className="text-white/80 mb-5 sm:mb-6 font-light text-xs sm:text-sm" style={{ fontFamily: 'var(--font-heading)' }}>
                        {t('homepage.footer.tagline', lang)}
                    </p>
                    <Link to={getLocalizedPath('/editorial-policy')}>
                        <Button 
                            variant="outline" 
                            className="border-white/40 text-white hover:bg-white hover:text-[#2C2C2C] rounded-none px-8 font-light tracking-wide text-sm transition-all duration-300"
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
