import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { t } from '@/i18n';
import { 
    ChefHat, Globe, Star, ArrowRight, Sparkles, 
    BookOpen, Shield, Languages, ScrollText, Archive
} from 'lucide-react';
import { toast } from 'sonner';

const HomePage = () => {
    const { language, getLocalizedPath } = useLanguage();
    const [bestRecipe, setBestRecipe] = useState(null);
    const [featuredRecipes, setFeaturedRecipes] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            // Pass language to get translated content
            const [bestRes, featuredRes] = await Promise.all([
                recipeAPI.getBest(language),
                recipeAPI.getFeatured(4, language)
            ]);
            
            setBestRecipe(bestRes.data.recipe);
            setFeaturedRecipes(featuredRes.data.recipes || []);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Failed to load content');
        } finally {
            setLoading(false);
        }
    }, [language]);

    useEffect(() => {
        loadData();
    }, [loadData]); // Re-fetch when language changes

    const getAuthenticityLabel = (level) => {
        switch(level) {
            case 1: return t('common.official', language);
            case 2: return t('common.traditional', language);
            case 3: return t('common.local', language);
            default: return t('common.traditional', language);
        }
    };

    return (
        <div className="min-h-screen" data-testid="homepage">
            {/* Banner */}
            <div className="bg-[#6A1F2E] text-white py-2 px-4 text-center text-sm">
                <span className="flex items-center justify-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    {t('home.banner', language)}
                    <Sparkles className="h-4 w-4" />
                </span>
            </div>

            {/* Hero Search Section */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="mb-6">
                        <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E]" />
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('home.title', language)}
                    </h1>
                    <p className="text-base sm:text-lg text-[#1E1E1E]/80 mb-8 max-w-2xl mx-auto">
                        {t('home.subtitle', language)}
                    </p>
                    <SearchBar className="max-w-2xl mx-auto" />
                </div>
            </section>

            {/* Editorial Mission Section */}
            <section className="bg-white py-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#6A1F2E]/10 mb-4">
                            <Archive className="h-7 w-7 text-[#6A1F2E]" />
                        </div>
                        <h2 className="text-3xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.mission.title', language)}
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto mb-6"></div>
                    </div>

                    <div className="prose prose-lg max-w-none mb-12">
                        <p className="text-[#1E1E1E]/80 text-center leading-relaxed text-lg">
                            {t('home.mission.intro', language)}
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8">
                        {/* Authenticity Without Compromise */}
                        <div className="bg-[#F5F2E8] rounded-xl p-8">
                            <div className="flex items-center gap-3 mb-4">
                                <Shield className="h-6 w-6 text-[#6A1F2E]" />
                                <h3 className="text-xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {t('home.mission.authenticity.title', language)}
                                </h3>
                            </div>
                            <p className="text-[#1E1E1E]/70 leading-relaxed">
                                {t('home.mission.authenticity.text', language)}
                            </p>
                        </div>

                        {/* A Living Archive */}
                        <div className="bg-[#F5F2E8] rounded-xl p-8">
                            <div className="flex items-center gap-3 mb-4">
                                <BookOpen className="h-6 w-6 text-[#6A1F2E]" />
                                <h3 className="text-xl font-semibold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {t('home.mission.purpose.title', language)}
                                </h3>
                            </div>
                            <p className="text-[#1E1E1E]/70 leading-relaxed">
                                {t('home.mission.purpose.text', language)}
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Language Philosophy Section */}
            <section className="bg-gradient-to-b from-[#FAF7F0] to-white py-16">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#3F4A3C]/10 mb-4">
                            <Languages className="h-7 w-7 text-[#3F4A3C]" />
                        </div>
                        <h2 className="text-3xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.languagePhilosophy.title', language)}
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto mb-6"></div>
                    </div>

                    <p className="text-[#1E1E1E]/80 text-center leading-relaxed text-lg mb-10 max-w-3xl mx-auto">
                        {t('home.languagePhilosophy.intro', language)}
                    </p>

                    <div className="bg-white rounded-xl shadow-sm border border-[#E5DCC3] p-8">
                        <ul className="space-y-4">
                            <li className="flex items-start gap-4">
                                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-semibold text-sm">1</span>
                                <p className="text-[#1E1E1E]/80 pt-1">{t('home.languagePhilosophy.point1', language)}</p>
                            </li>
                            <li className="flex items-start gap-4">
                                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-semibold text-sm">2</span>
                                <p className="text-[#1E1E1E]/80 pt-1">{t('home.languagePhilosophy.point2', language)}</p>
                            </li>
                            <li className="flex items-start gap-4">
                                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-semibold text-sm">3</span>
                                <p className="text-[#1E1E1E]/80 pt-1">{t('home.languagePhilosophy.point3', language)}</p>
                            </li>
                            <li className="flex items-start gap-4">
                                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-[#6A1F2E] text-white flex items-center justify-center font-semibold text-sm">4</span>
                                <p className="text-[#1E1E1E]/80 pt-1">{t('home.languagePhilosophy.point4', language)}</p>
                            </li>
                        </ul>

                        <div className="mt-8 pt-6 border-t border-[#E5DCC3]">
                            <p className="text-[#1E1E1E] text-center font-medium italic">
                                {t('home.languagePhilosophy.conclusion', language)}
                            </p>
                        </div>
                    </div>

                    {/* Available Languages */}
                    <div className="flex justify-center gap-4 mt-8 flex-wrap">
                        {[
                            { code: 'en', flag: 'EN', name: 'English' },
                            { code: 'it', flag: '🇮🇹', name: 'Italiano' },
                            { code: 'fr', flag: '🇫🇷', name: 'Français' },
                            { code: 'es', flag: '🇪🇸', name: 'Español' },
                            { code: 'de', flag: '🇩🇪', name: 'Deutsch' }
                        ].map((lang) => (
                            <Badge 
                                key={lang.code} 
                                variant="outline" 
                                className={`px-4 py-2 text-sm ${language === lang.code ? 'bg-[#6A1F2E] text-white border-[#6A1F2E]' : 'border-[#E5DCC3]'}`}
                            >
                                {lang.flag} {lang.name}
                            </Badge>
                        ))}
                    </div>
                </div>
            </section>

            {/* Best Recipe Worldwide - Hero */}
            {bestRecipe && (
                <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            🏆 {t('home.bestRecipe', language)}
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto"></div>
                    </div>

                    <Link to={getLocalizedPath(`/recipe/${bestRecipe.slug}`)} className="block">
                        <div className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300" data-testid="best-recipe-hero">
                            <div className="grid md:grid-cols-2 gap-0">
                                {/* Image/Placeholder */}
                                <div className="relative h-64 md:h-96 bg-gradient-to-br from-[#6A1F2E] to-[#3F4A3C] flex items-center justify-center">
                                    {bestRecipe.photos && bestRecipe.photos[0]?.image_url ? (
                                        <img 
                                            src={bestRecipe.photos[0].image_url} 
                                            alt={bestRecipe.recipe_name}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <ChefHat className="h-24 w-24 text-white/30" />
                                    )}
                                    <div className="absolute top-4 left-4 flex gap-2">
                                        <Badge className="bg-[#CBA55B] text-white">
                                            <Star className="h-3 w-3 mr-1 fill-current" />
                                            {bestRecipe.average_rating?.toFixed(1) || '4.5'}
                                        </Badge>
                                        <Badge className="bg-[#6A1F2E] text-white">
                                            {getAuthenticityLabel(bestRecipe.authenticity_level)}
                                        </Badge>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-8 flex flex-col justify-center">
                                    <div className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-3">
                                        <Globe className="h-4 w-4" />
                                        <span>{bestRecipe.origin_country || bestRecipe.country}</span>
                                        <span>•</span>
                                        <span>{bestRecipe.origin_region || bestRecipe.region}</span>
                                    </div>

                                    <h3 className="text-3xl font-bold text-[#1E1E1E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        {bestRecipe.recipe_name || bestRecipe.title_original}
                                    </h3>

                                    <p className="text-[#1E1E1E]/70 mb-6 line-clamp-3">
                                        {bestRecipe.characteristic_profile || bestRecipe.history_summary || bestRecipe.origin_story}
                                    </p>

                                    <div className="flex items-center gap-4 text-sm text-[#1E1E1E]/60 mb-6">
                                        <span>{bestRecipe.ratings_count || 0} {t('home.reviews', language)}</span>
                                        <span>•</span>
                                        <span>{bestRecipe.favorites_count || 0} {t('home.favorites', language)}</span>
                                    </div>

                                    <Button className="btn-elegant w-fit">
                                        {t('home.viewRecipe', language)} <ArrowRight className="ml-2 h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </Link>
                </section>
            )}

            {/* Featured Recipes */}
            <section className="bg-white py-16">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.featured', language)}
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto"></div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12" data-testid="loading-state">
                            <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                            <p className="text-[#1E1E1E]/60">{t('home.loading', language)}</p>
                        </div>
                    ) : featuredRecipes.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="featured-recipes-grid">
                            {featuredRecipes.map((recipe) => (
                                <RecipeCard key={recipe.slug} recipe={recipe} />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 card-elegant" data-testid="no-recipes-state">
                            <p className="text-[#1E1E1E]/60 mb-4">{t('home.noRecipes', language)}</p>
                        </div>
                    )}

                    {/* View More Button */}
                    <div className="text-center mt-12">
                        <Link to={getLocalizedPath('/explore')}>
                            <Button className="btn-elegant" size="lg" data-testid="view-more-btn">
                                {t('home.viewMore', language)} <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#6A1F2E] text-white mb-4">
                            <Star className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.features.authenticity.title', language)}
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            {t('home.features.authenticity.description', language)}
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#3F4A3C] text-white mb-4">
                            <Globe className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.features.global.title', language)}
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            {t('home.features.global.description', language)}
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#CBA55B] text-white mb-4">
                            <ChefHat className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {t('home.features.ai.title', language)}
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            {t('home.features.ai.description', language)}
                        </p>
                    </div>
                </div>
            </section>

            {/* Editorial Policy CTA */}
            <section className="bg-[#1E1E1E] text-white py-16">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                    <ScrollText className="h-10 w-10 mx-auto mb-4 text-[#CBA55B]" />
                    <h2 className="text-2xl font-bold mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {t('footer.editorial', language)}
                    </h2>
                    <p className="text-white/70 mb-6 max-w-2xl mx-auto">
                        {language === 'en' 
                            ? 'Learn about our commitment to authenticity, our source verification process, and our strict editorial standards.'
                            : language === 'it'
                            ? 'Scopri il nostro impegno per l\'autenticità, il nostro processo di verifica delle fonti e i nostri rigorosi standard editoriali.'
                            : language === 'fr'
                            ? 'Découvrez notre engagement envers l\'authenticité, notre processus de vérification des sources et nos normes éditoriales strictes.'
                            : language === 'es'
                            ? 'Conozca nuestro compromiso con la autenticidad, nuestro proceso de verificación de fuentes y nuestros estrictos estándares editoriales.'
                            : 'Erfahren Sie mehr über unser Engagement für Authentizität, unseren Quellenverifizierungsprozess und unsere strengen redaktionellen Standards.'
                        }
                    </p>
                    <Link to={getLocalizedPath('/editorial-policy')}>
                        <Button variant="outline" className="border-white text-white hover:bg-white hover:text-[#1E1E1E]">
                            {t('common.learnMore', language)} <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </Link>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
