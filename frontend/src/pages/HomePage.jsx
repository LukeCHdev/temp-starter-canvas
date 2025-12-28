import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI, continentAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';
import { 
    Globe, ArrowRight, Search, CheckCircle2, Users, MessageSquare
} from 'lucide-react';
import { toast } from 'sonner';

// Dish type categories for browse section
const DISH_TYPES = [
    { key: 'appetizer', en: 'Appetizers', it: 'Antipasti', slug: 'appetizer' },
    { key: 'aperitif', en: 'Aperitif & Small Plates', it: 'Aperitivi e Stuzzichini', slug: 'aperitif' },
    { key: 'first-course', en: 'First Courses', it: 'Primi Piatti', slug: 'first-course' },
    { key: 'main-course', en: 'Main Courses', it: 'Secondi Piatti', slug: 'main-course' },
    { key: 'side-dish', en: 'Side Dishes', it: 'Contorni', slug: 'side-dish' },
    { key: 'dessert', en: 'Desserts', it: 'Dolci', slug: 'dessert' },
    { key: 'street-food', en: 'Street Food', it: 'Cibo di Strada', slug: 'street-food' },
    { key: 'festive', en: 'Festive & Ritual Dishes', it: 'Piatti Festivi e Rituali', slug: 'festive' },
];

const HomePage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const [featuredRecipe, setFeaturedRecipe] = useState(null);
    const [curatedRecipes, setCuratedRecipes] = useState([]);
    const [continentStats, setContinentStats] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            const [bestRes, featuredRes, continentsRes] = await Promise.all([
                recipeAPI.getBest(language),
                recipeAPI.getFeatured(6, language),
                continentAPI.getAll()
            ]);
            
            setFeaturedRecipe(bestRes.data.recipe);
            setCuratedRecipes(featuredRes.data.recipes || []);
            setContinentStats(continentsRes.data.continents || []);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Failed to load content');
        } finally {
            setLoading(false);
        }
    }, [language]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const getAuthenticityLabel = (level) => {
        switch(level) {
            case 1: return 'Officially Recognized';
            case 2: return 'Tradition-Verified';
            case 3: return 'Regional Heritage';
            default: return 'Tradition-Verified';
        }
    };

    const getDishTypeName = (type) => {
        return language === 'it' ? type.it : type.en;
    };

    return (
        <div className="min-h-screen bg-[#FDFBF7]" data-testid="homepage">
            
            {/* ============================================ */}
            {/* 1. VALUE STRIP - Calm, Editorial Positioning */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] border-b border-[#E8E4DC] py-6">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-[#2C2C2C] text-lg font-light tracking-wide" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        A curated collection of authentic recipes, selected for tradition — not volume.
                    </p>
                    <div className="flex justify-center gap-8 mt-4 text-sm text-[#5C5C5C] flex-wrap">
                        <span className="flex items-center gap-2">
                            <Globe className="h-4 w-4 text-[#6A1F2E]" />
                            Curated global recipes
                        </span>
                        <span className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-[#6A1F2E]" />
                            Community-validated for authenticity
                        </span>
                        <span className="flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4 text-[#6A1F2E]" />
                            Cultural accuracy over popularity
                        </span>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 2. HERO SEARCH - Clean, Centered, Editorial */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16 px-4">
                <div className="max-w-3xl mx-auto text-center">
                    <h1 className="text-5xl sm:text-6xl font-light text-[#2C2C2C] mb-6 tracking-tight" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Sous Chef Linguine
                    </h1>
                    <p className="text-lg text-[#5C5C5C] mb-10 font-light">
                        The culinary archive of authentic regional recipes
                    </p>
                    
                    {/* Search Bar */}
                    <div className="relative max-w-2xl mx-auto">
                        <SearchBar className="w-full" />
                        <p className="text-sm text-[#7C7C7C] mt-3 font-light">
                            Search by recipe, ingredient, region, tradition, or dish type
                        </p>
                        <p className="text-xs text-[#9C9C9C] mt-2 italic">
                            Can't find what you're looking for? Try our cultural search — it often reveals dishes you don't know by name.
                        </p>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 3. FEATURED RECIPE HERO - Single Featured Recipe */}
            {/* ============================================ */}
            {featuredRecipe && !loading && (
                <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <Link to={getLocalizedPath(`/recipe/${featuredRecipe.slug}`)} className="block group">
                        <div className="bg-white border border-[#E8E4DC] overflow-hidden" data-testid="featured-recipe-hero">
                            <div className="grid md:grid-cols-2">
                                {/* Image */}
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

                                {/* Content */}
                                <div className="p-8 md:p-10 flex flex-col justify-center bg-white">
                                    <div className="mb-4">
                                        <span className="inline-block text-xs uppercase tracking-widest text-[#6A1F2E] font-medium border border-[#6A1F2E] px-3 py-1">
                                            {getAuthenticityLabel(featuredRecipe.authenticity_level)}
                                        </span>
                                    </div>

                                    <div className="text-sm text-[#7C7C7C] mb-3 tracking-wide">
                                        {featuredRecipe.origin_country || featuredRecipe.country}
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
                                        <span>Explore recipe</span>
                                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Link>
                </section>
            )}

            {/* ============================================ */}
            {/* 4. HOW AUTHENTICITY WORKS - Key USP Section */}
            {/* ============================================ */}
            <section className="bg-white py-16 border-t border-b border-[#E8E4DC]">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h2 className="text-2xl font-light text-center text-[#2C2C2C] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        How Authenticity Works
                    </h2>
                    <div className="w-16 h-px bg-[#6A1F2E] mx-auto mb-10"></div>

                    <div className="grid md:grid-cols-3 gap-10">
                        {/* Step 1 */}
                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">1</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Curated Selection
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                Recipes are selected based on historical and regional authenticity.
                            </p>
                        </div>

                        {/* Step 2 */}
                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">2</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Community Validation
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                Users vote on how faithfully a recipe respects its traditional form.
                            </p>
                        </div>

                        {/* Step 3 */}
                        <div className="text-center">
                            <div className="w-10 h-10 rounded-full border-2 border-[#6A1F2E] flex items-center justify-center mx-auto mb-4">
                                <span className="text-[#6A1F2E] font-medium text-sm">3</span>
                            </div>
                            <h3 className="text-base font-medium text-[#2C2C2C] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Cultural Correction
                            </h3>
                            <p className="text-sm text-[#5C5C5C] leading-relaxed font-light">
                                Users may suggest corrections when a recipe does not meet tradition.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 5. BROWSE BY CONTINENT - PRIMARY DISCOVERY (MOVED UP) */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Browse by Continent
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto"></div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {[
                            { name: 'Europe', slug: 'europe' },
                            { name: 'Asia', slug: 'asia' },
                            { name: 'Americas', slug: 'americas' },
                            { name: 'Africa', slug: 'africa' },
                            { name: 'Middle East', slug: 'middle-east' },
                            { name: 'Oceania', slug: 'oceania' },
                        ].map((continent) => {
                            const stats = continentStats.find(c => 
                                c.name?.toLowerCase() === continent.name.toLowerCase() ||
                                c.continent?.toLowerCase() === continent.name.toLowerCase()
                            );
                            const count = stats?.recipe_count || stats?.count || 0;
                            
                            return (
                                <Link 
                                    key={continent.slug}
                                    to={getLocalizedPath(`/explore/${continent.slug}`)}
                                    className="group block p-6 bg-white border border-[#E8E4DC] hover:border-[#6A1F2E] transition-colors text-center"
                                >
                                    <h3 className="text-lg font-light text-[#2C2C2C] mb-1 group-hover:text-[#6A1F2E] transition-colors" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        {continent.name}
                                    </h3>
                                    <p className="text-xs text-[#7C7C7C]">
                                        {count} recipes
                                    </p>
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 6. BROWSE BY DISH TYPE - ACTIONABLE (MOVED UP) */}
            {/* ============================================ */}
            <section className="bg-white py-16 border-t border-[#E8E4DC]">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Browse by Dish Type
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto mb-3"></div>
                        <p className="text-[#5C5C5C] font-light text-sm">
                            Explore recipes by their traditional culinary category
                        </p>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {DISH_TYPES.map((type) => (
                            <Link 
                                key={type.key}
                                to={getLocalizedPath(`/explore?dishType=${type.slug}`)}
                                className="group block p-4 text-center border border-[#E8E4DC] bg-[#FDFBF7] hover:border-[#6A1F2E] hover:bg-white transition-all"
                            >
                                <span className="text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors font-light text-sm" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {getDishTypeName(type)}
                                </span>
                            </Link>
                        ))}
                    </div>

                    <div className="text-center mt-8">
                        <p className="text-xs text-[#9C9C9C] font-light italic max-w-xl mx-auto">
                            You can also search by dish type — appetizer, first course, main dish, dessert — even when names vary by culture.
                        </p>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 7. CURATED RECIPES - Limited, Intentional (MOVED DOWN) */}
            {/* ============================================ */}
            <section className="bg-[#FDFBF7] py-16 border-t border-[#E8E4DC]">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Curated Recipes
                        </h2>
                        <div className="w-16 h-px bg-[#6A1F2E] mx-auto mb-3"></div>
                        <p className="text-[#5C5C5C] font-light text-sm">
                            Selected for authenticity, verified by tradition
                        </p>
                    </div>

                    {loading ? (
                        <div className="text-center py-12" data-testid="loading-state">
                            <p className="text-[#7C7C7C] font-light">Loading curated collection...</p>
                        </div>
                    ) : curatedRecipes.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="curated-recipes-grid">
                            {curatedRecipes.slice(0, 6).map((recipe) => (
                                <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12" data-testid="no-recipes-state">
                            <p className="text-[#7C7C7C] font-light">Curating our collection...</p>
                        </div>
                    )}

                    <div className="text-center mt-10">
                        <Link to={getLocalizedPath('/explore')}>
                            <Button 
                                variant="outline" 
                                className="border-[#6A1F2E] text-[#6A1F2E] hover:bg-[#6A1F2E] hover:text-white px-8 py-2 rounded-none font-light tracking-wide text-sm"
                                data-testid="explore-all-btn"
                            >
                                Explore Full Collection
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* ============================================ */}
            {/* 8. FOOTER CTA - Quiet Authority */}
            {/* ============================================ */}
            <section className="bg-[#2C2C2C] py-14">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <h2 className="text-xl font-light text-white mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Our Editorial Standards
                    </h2>
                    <p className="text-white/60 mb-6 font-light text-sm leading-relaxed">
                        Learn about our commitment to authenticity, our source verification process, and our strict editorial standards for preserving culinary heritage.
                    </p>
                    <Link to={getLocalizedPath('/editorial-policy')}>
                        <Button 
                            variant="outline" 
                            className="border-white/40 text-white hover:bg-white hover:text-[#2C2C2C] rounded-none px-8 font-light tracking-wide text-sm"
                        >
                            Read Our Policy
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
