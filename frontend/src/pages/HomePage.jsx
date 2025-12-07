import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '@/components/common/SearchBar';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { recipeAPI, regionAPI } from '@/utils/api';
import { Button } from '@/components/ui/button';
import { ChefHat, Globe, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

const HomePage = () => {
    const [featuredRecipes, setFeaturedRecipes] = useState([]);
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            // Load featured recipes
            const recipesRes = await recipeAPI.getAll({ page: 1, limit: 6 });
            setFeaturedRecipes(recipesRes.data.recipes || []);

            // Load regions
            const regionsRes = await regionAPI.getAll();
            setRegions(regionsRes.data.regions || []);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('Failed to load content');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen" data-testid="homepage">
            {/* Hero Section */}
            <section className="relative bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-20 px-4">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="mb-6">
                        <ChefHat className="h-16 w-16 mx-auto text-[#6A1F2E]" />
                    </div>
                    <h1 className="mb-6 text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        The Authentic Global Recipe Engine
                    </h1>
                    <p className="text-lg sm:text-xl text-[#1E1E1E]/80 mb-8 max-w-2xl mx-auto leading-relaxed">
                        Discover genuine, traditional recipes from every corner of the world. 
                        Each dish validated for cultural authenticity and accompanied by warm, 
                        sensory storytelling from Sous Chef Linguine.
                    </p>
                    <SearchBar className="max-w-2xl mx-auto" />
                </div>
            </section>

            {/* Featured Recipes */}
            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                <div className="text-center mb-12">
                    <h2 className="text-[#1E1E1E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        Featured Authentic Recipes
                    </h2>
                    <div className="gold-divider"></div>
                </div>

                {loading ? (
                    <div className="text-center py-12" data-testid="loading-state">
                        <p className="text-[#1E1E1E]/60">Loading recipes...</p>
                    </div>
                ) : featuredRecipes.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" data-testid="featured-recipes-grid">
                        {featuredRecipes.map((recipe) => (
                            <RecipeCard key={recipe.slug} recipe={recipe} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12 card-elegant" data-testid="no-recipes-state">
                        <p className="text-[#1E1E1E]/60 mb-4">No recipes available yet.</p>
                        <p className="text-sm text-[#1E1E1E]/50">Our AI is cooking up authentic recipes. Check back soon!</p>
                    </div>
                )}
            </section>

            {/* Regions Browser */}
            <section className="bg-white py-16">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <h2 className="text-[#1E1E1E] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Explore by Region
                        </h2>
                        <div className="gold-divider"></div>
                        <p className="narrative-text max-w-2xl mx-auto mt-6">
                            Journey through the world's culinary traditions, region by region. 
                            Each area tells its own delicious story.
                        </p>
                    </div>

                    {regions.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="regions-grid">
                            {regions.slice(0, 6).map((region) => (
                                <Link
                                    key={region.slug}
                                    to={`/regions#${region.slug}`}
                                    className="card-elegant group"
                                    data-testid={`region-card-${region.slug}`}
                                >
                                    <Globe className="h-8 w-8 text-[#CBA55B] mb-3" />
                                    <h3 className="text-xl font-semibold mb-2 group-hover:text-[#6A1F2E] transition-colors">
                                        {region.name}
                                    </h3>
                                    <p className="text-sm text-[#1E1E1E]/70 line-clamp-2">
                                        {region.description}
                                    </p>
                                </Link>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12" data-testid="no-regions-state">
                            <p className="text-[#1E1E1E]/60">Regions loading...</p>
                        </div>
                    )}

                    <div className="text-center mt-12">
                        <Link to="/regions">
                            <Button className="btn-elegant" data-testid="view-all-regions-btn">
                                View All Regions
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#6A1F2E] text-white mb-4">
                            <ChefHat className="h-8 w-8" />
                        </div>
                        <h3 className="text-xl font-semibold mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Authenticity First
                        </h3>
                        <p className="narrative-text text-sm">
                            Every recipe validated through our strict 3-tier authenticity system, 
                            ensuring cultural accuracy and traditional integrity.
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#3F4A3C] text-white mb-4">
                            <Globe className="h-8 w-8" />
                        </div>
                        <h3 className="text-xl font-semibold mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Global Coverage
                        </h3>
                        <p className="narrative-text text-sm">
                            Explore traditional dishes from every region and country, 
                            with recipes sourced from native-language documentation.
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#CBA55B] text-white mb-4">
                            <BookOpen className="h-8 w-8" />
                        </div>
                        <h3 className="text-xl font-semibold mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Warm Storytelling
                        </h3>
                        <p className="narrative-text text-sm">
                            Each recipe comes alive through Sous Chef Linguini's warm, 
                            sensory narration — turning cooking into an emotional journey.
                        </p>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default HomePage;