import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChefHat, Globe, Star, ArrowRight, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const HomePage = () => {
    const [bestRecipe, setBestRecipe] = useState(null);
    const [featuredRecipes, setFeaturedRecipes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Load best recipe and featured in parallel
            const [bestRes, featuredRes] = await Promise.all([
                recipeAPI.getBest(),
                recipeAPI.getFeatured(4)
            ]);
            
            setBestRecipe(bestRes.data.recipe);
            setFeaturedRecipes(featuredRes.data.recipes || []);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Failed to load content');
        } finally {
            setLoading(false);
        }
    };

    const getAuthenticityLabel = (level) => {
        switch(level) {
            case 1: return 'Official';
            case 2: return 'Traditional';
            case 3: return 'Local';
            default: return 'Traditional';
        }
    };

    return (
        <div className="min-h-screen" data-testid="homepage">
            {/* Optional Banner */}
            <div className="bg-[#6A1F2E] text-white py-2 px-4 text-center text-sm">
                <span className="flex items-center justify-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Authentic Regional Recipes Powered by Sous-Chef Linguine
                    <Sparkles className="h-4 w-4" />
                </span>
            </div>

            {/* Search Section */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="mb-6">
                        <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E]" />
                    </div>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-4 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Sous Chef Linguine
                    </h1>
                    <p className="text-base sm:text-lg text-[#1E1E1E]/80 mb-8 max-w-2xl mx-auto">
                        The Authentic Global Recipe Engine
                    </p>
                    <SearchBar className="max-w-2xl mx-auto" />
                </div>
            </section>

            {/* Best Recipe Worldwide - Hero */}
            {bestRecipe && (
                <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                    <div className="text-center mb-8">
                        <h2 className="text-3xl font-bold text-[#1E1E1E] mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            🏆 Best Recipe Worldwide
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto"></div>
                    </div>

                    <Link to={`/recipe/${bestRecipe.slug}`} className="block">
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
                                        <span>{bestRecipe.ratings_count || 0} reviews</span>
                                        <span>•</span>
                                        <span>{bestRecipe.favorites_count || 0} favorites</span>
                                    </div>

                                    <Button className="btn-elegant w-fit">
                                        View Recipe <ArrowRight className="ml-2 h-4 w-4" />
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
                            Featured Authentic Recipes
                        </h2>
                        <div className="w-24 h-1 bg-[#CBA55B] mx-auto"></div>
                    </div>

                    {loading ? (
                        <div className="text-center py-12" data-testid="loading-state">
                            <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                            <p className="text-[#1E1E1E]/60">Loading recipes...</p>
                        </div>
                    ) : featuredRecipes.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="featured-recipes-grid">
                            {featuredRecipes.map((recipe) => (
                                <RecipeCard key={recipe.slug} recipe={recipe} />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 card-elegant" data-testid="no-recipes-state">
                            <p className="text-[#1E1E1E]/60 mb-4">No recipes available yet.</p>
                        </div>
                    )}

                    {/* View More Button */}
                    <div className="text-center mt-12">
                        <Link to="/explore">
                            <Button className="btn-elegant" size="lg" data-testid="view-more-btn">
                                View More Recipes <ArrowRight className="ml-2 h-4 w-4" />
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
                            Authenticity First
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            Every recipe validated through strict authenticity ranking.
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#3F4A3C] text-white mb-4">
                            <Globe className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Global Coverage
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            Traditional dishes from every corner of the world.
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#CBA55B] text-white mb-4">
                            <ChefHat className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            AI-Powered
                        </h3>
                        <p className="text-sm text-[#1E1E1E]/70">
                            On-demand recipe generation by Sous-Chef Linguine.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default HomePage;
