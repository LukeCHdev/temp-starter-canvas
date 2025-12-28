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

// Dish type keys for translation lookup
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

// Continents for browsing
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

    // Translated authenticity labels
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
            
            {/* ============================================ */}
            {/* VALUE STRIP */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] border-b border-[#E8E4DC] py-6">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-[#2C2C2C] text-lg font-light tracking-wide" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('homepage.valueStrip.main', lang)}
                    </p>
                    <div className="flex justify-center gap-8 mt-4 text-sm text-[#5C5C5C] flex-wrap">
                        <span className="flex items-center gap-2">
                            <Globe className="h-4 w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.curated', lang)}
                        </span>
                        <span className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.validated', lang)}
                        </span>
                        <span className="flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4 text-[#6A1F2E]" />
                            {t('homepage.valueStrip.accuracy', lang)}
                        </span>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* HERO SEARCH */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16 px-4">
                <div className="max-w-3xl mx-auto text-center">
                    <h1 className="text-5xl sm:text-6xl font-light text-[#2C2C2C] mb-6 tracking-tight" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('homepage.hero.title', lang)}
                    </h1>
                    <p className="text-lg text-[#5C5C5C] mb-10 font-light">
                        {t('homepage.hero.subtitle', lang)}
                    </p>
                    
                    <div className="relative max-w-2xl mx-auto">
                        <SearchBar className="w-full" />
                        <p className="text-xs text-[#9C9C9C] mt-3 font-light">
                            {t('homepage.hero.searchHelper', lang)}
                        </p>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* FEATURED RECIPE HERO */}
            {/* ============================================ */}
            {featuredRecipe && !loading && (
                <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <Link to={getLocalizedPath(`/recipe/${featuredRecipe.slug}`)} className="block group">
                        <div className="bg-white border border-[#E8E4DC] overflow-hidden" data-testid="featured-recipe-hero">
                            <div className="grid md:grid-cols-2">
                                <div className="relative h-72 md:h-[380px] bg-[#F5F2EC] overflow-hidden">
                                    {featuredRecipe.photos && featuredRecipe.photos[0]?.image_url ? (
                                        <img 
                                            src={featuredRecipe.photos[0].image_url} 
                                            alt={featuredRecipe.recipe_name}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center">
                                            <span className="text-[#BFBFBF] text-6xl font-light" style={{ fontFamily: 'Cormorant Garamond, serif' }}>SCL</span>
                                        </div>
                                    )}
                                </div>

                                <div className="p-8 md:p-10 flex flex-col justify-center bg-white">
                                    <div className="mb-4">
                                        <span className="inline-block text-xs uppercase tracking-widest text-[#6A1F2E] font-medium border border-[#6A1F2E] px-3 py-1">
                                            {getAuthenticityLabel(featuredRecipe.authenticity_level)}
                                        </span>
                                    </div>

                                    <div className="text-sm text-[#7C7C7C] mb-3 tracking-wide">
                                        {t(`countries.${featuredRecipe.origin_country || featuredRecipe.country}`, lang)}
                                        {(featuredRecipe.origin_region || featuredRecipe.region) && (
                                            <span> · {featuredRecipe.origin_region || featuredRecipe.region}</span>
                                        )}
                                    </div>

                                    <h2 className="text-2xl md:text-3xl font-light text-[#2C2C2C] mb-4 leading-tight" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        {featuredRecipe.recipe_name || featuredRecipe.title_original}
                                    </h2>

                                    <p className="text-[#5C5C5C] mb-6 leading-relaxed line-clamp-3 font-light text-sm">
                                        {featuredRecipe.characteristic_profile || featuredRecipe.history_summary || featuredRecipe.origin_story}
                                    </p>

                                    <div className="flex items-center text-[#6A1F2E] font-medium group-hover:gap-3 transition-all text-sm">
                                        <span>{t('homepage.hero.exploreRecipe', lang)}</span>
                                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Link>
                </section>
            )}

            {/* ============================================ */}
            {/* HOW AUTHENTICITY WORKS */}
            {/* ============================================ */}
            <section className="bg-white py-16 border-t border-b border-[#E8E4DC]">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-2xl font-light text-center text-[#2C2C2C] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('homepage.authenticity.title', lang)}
                    </h2>
                    <div className="w-16 h-px bg-[#6A1F2E] mx-auto mb-10"></div>

                    <div className="grid md:grid-cols-3 gap-10">
                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">1</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                {t('homepage.authenticity.step1Title', lang)}
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                {t('homepage.authenticity.step1Text', lang)}
                            </p>
                        </div>

                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">2</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                {t('homepage.authenticity.step2Title', lang)}
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                {t('homepage.authenticity.step2Text', lang)}
                            </p>
                        </div>

                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">3</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                {t('homepage.authenticity.step3Title', lang)}
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                {t('homepage.authenticity.step3Text', lang)}
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* BROWSE BY CONTINENT */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('homepage.browseContinent.title', lang)}
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto"></div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {CONTINENT_KEYS.map((continent) => (
                            <Link 
                                key={continent.slug}
                                to={getLocalizedPath(`/explore/${continent.slug}`)}
                                className="group block p-6 bg-white border border-[#E8E4DC] hover:border-[#6A1F2E] transition-colors text-center"
                            >
                                <h3 className="text-lg font-light text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {t(`continents.${continent.key}`, lang)}
                                </h3>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* BROWSE BY DISH TYPE */}
            {/* ============================================ */}
            <section className="bg-white py-16 border-t border-[#E8E4DC]">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('homepage.browseDishType.title', lang)}
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto"></div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {DISH_TYPE_KEYS.map((type) => (
                            <Link 
                                key={type.key}
                                to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                className="group block p-4 text-center border border-[#E8E4DC] bg-[#FDFBF7] hover:border-[#6A1F2E] hover:bg-white transition-all"
                            >
                                <span className="text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors font-light text-sm" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {t(`homepage.dishTypes.${type.key}`, lang)}
                                </span>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* CURATED RECIPES */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16 border-t border-[#E8E4DC]">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('homepage.curatedRecipes.title', lang)}
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto"></div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12" data-testid="loading-state">
                            <p className="text-[#7C7C7C] font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                        </div>
                    ) : curatedRecipes.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="curated-recipes-grid">
                            {curatedRecipes.slice(0, 6).map((recipe) => (
                                <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12" data-testid="no-recipes-state">
                            <p className="text-[#7C7C7C] font-light">{t('homepage.curatedRecipes.loading', lang)}</p>
                        </div>
                    )}

                    <div className="text-center mt-10">
                        <Link to={getLocalizedPath('/explore')}>
                            <Button 
                                variant="outline" 
                                className="border-[#6A1F2E] text-[#6A1F2E] hover:bg-[#6A1F2E] hover:text-white px-8 py-2 rounded-none font-light tracking-wide text-sm"
                                data-testid="explore-all-btn"
                            >
                                {t('homepage.curatedRecipes.exploreAll', lang)}
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* FOOTER CTA */}
            {/* ============================================ */}
            <section className="bg-[#2C2C2C] py-14">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <p className="text-white/80 mb-6 font-light text-sm" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('homepage.footer.tagline', lang)}
                    </p>
                    <Link to={getLocalizedPath('/editorial-policy')}>
                        <Button 
                            variant="outline" 
                            className="border-white/40 text-white hover:bg-white hover:text-[#2C2C2C] rounded-none px-8 font-light tracking-wide text-sm"
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
