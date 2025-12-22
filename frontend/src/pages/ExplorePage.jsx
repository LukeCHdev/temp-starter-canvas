import React, { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI, continentAPI } from '@/utils/api';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChefHat, Globe, MapPin, ChevronRight, Home } from 'lucide-react';
import { toast } from 'sonner';

// Continent flags/emojis
const CONTINENT_INFO = {
    'Europe': { emoji: '🇪🇺', color: 'bg-blue-500' },
    'Asia': { emoji: '🌏', color: 'bg-red-500' },
    'Americas': { emoji: '🌎', color: 'bg-green-500' },
    'Africa': { emoji: '🌍', color: 'bg-yellow-500' },
    'Middle East': { emoji: '🕌', color: 'bg-orange-500' },
    'Oceania': { emoji: '🦘', color: 'bg-purple-500' },
};

const ExplorePage = () => {
    const { continent, country } = useParams();
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();
    
    const [topRecipes, setTopRecipes] = useState([]);
    const [continents, setContinents] = useState([]);
    const [countries, setCountries] = useState([]);
    const [countryRecipes, setCountryRecipes] = useState([]);
    const [selectedContinent, setSelectedContinent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [pageTitle, setPageTitle] = useState(t('explore.title'));

    useEffect(() => {
        if (country) {
            loadCountryData(country, continent);
        } else if (continent) {
            loadContinentData(continent);
        } else {
            loadExploreData();
        }
    }, [continent, country]);

    const loadExploreData = async () => {
        setLoading(true);
        try {
            const [topRes, continentRes] = await Promise.all([
                recipeAPI.getTopWorldwide(10),
                continentAPI.getAll()
            ]);
            
            setTopRecipes(topRes.data.recipes || []);
            setContinents(continentRes.data.continents || []);
            setPageTitle(t('explore.title'));
            setSelectedContinent(null);
            setCountries([]);
            setCountryRecipes([]);
        } catch (error) {
            console.error('Error loading explore data:', error);
            toast.error('Failed to load data');
        } finally {
            setLoading(false);
        }
    };

    const loadContinentData = async (continentSlug) => {
        setLoading(true);
        try {
            const [countriesRes, continentRes] = await Promise.all([
                continentAPI.getCountries(continentSlug),
                continentAPI.getAll()
            ]);
            
            setCountries(countriesRes.data.countries || []);
            setContinents(continentRes.data.continents || []);
            setSelectedContinent(countriesRes.data.continent);
            setPageTitle(countriesRes.data.continent);
            setCountryRecipes([]);
        } catch (error) {
            console.error('Error loading continent data:', error);
            toast.error('Failed to load countries');
        } finally {
            setLoading(false);
        }
    };

    const loadCountryData = async (countrySlug, continentSlug) => {
        setLoading(true);
        try {
            const res = await recipeAPI.getByCountryName(countrySlug);
            setCountryRecipes(res.data.recipes || []);
            setSelectedContinent(res.data.continent);
            setPageTitle(res.data.country);
        } catch (error) {
            console.error('Error loading country data:', error);
            toast.error('Failed to load recipes');
        } finally {
            setLoading(false);
        }
    };

    const handleContinentSelect = (continentSlug) => {
        navigate(`/explore/${continentSlug}`);
    };

    // Breadcrumb component
    const Breadcrumb = () => (
        <nav className="flex items-center gap-2 text-sm text-[#1E1E1E]/60 mb-6" aria-label="Breadcrumb">
            <Link to="/" className="hover:text-[#6A1F2E] flex items-center gap-1">
                <Home className="h-4 w-4" />
                Home
            </Link>
            <ChevronRight className="h-4 w-4" />
            <Link to="/explore" className={`hover:text-[#6A1F2E] ${!continent ? 'text-[#6A1F2E] font-medium' : ''}`}>
                Explore
            </Link>
            {continent && (
                <>
                    <ChevronRight className="h-4 w-4" />
                    <Link 
                        to={`/explore/${continent}`} 
                        className={`hover:text-[#6A1F2E] ${!country ? 'text-[#6A1F2E] font-medium' : ''}`}
                    >
                        {selectedContinent || continent.replace('-', ' ')}
                    </Link>
                </>
            )}
            {country && (
                <>
                    <ChevronRight className="h-4 w-4" />
                    <span className="text-[#6A1F2E] font-medium">
                        {pageTitle}
                    </span>
                </>
            )}
        </nav>
    );

    return (
        <div className="min-h-screen bg-[#FAF7F0]" data-testid="explore-page">
            {/* Header */}
            <section className="bg-gradient-to-b from-[#F5F2E8] to-[#FAF7F0] py-12 px-4">
                <div className="max-w-6xl mx-auto">
                    <Breadcrumb />
                    <h1 className="text-4xl sm:text-5xl font-bold text-[#1E1E1E]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {pageTitle}
                    </h1>
                    {!country && !continent && (
                        <p className="text-[#1E1E1E]/70 mt-4">
                            Discover authentic recipes from around the world
                        </p>
                    )}
                </div>
            </section>

            <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {loading ? (
                    <div className="text-center py-12">
                        <ChefHat className="h-12 w-12 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                        <p className="text-[#1E1E1E]/60">Loading...</p>
                    </div>
                ) : country ? (
                    /* Country Recipes View */
                    <>
                        <div className="flex items-center gap-3 mb-8">
                            <MapPin className="h-6 w-6 text-[#6A1F2E]" />
                            <span className="text-lg text-[#1E1E1E]/70">
                                {countryRecipes.length} recipes from {pageTitle}
                            </span>
                        </div>

                        {countryRecipes.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {countryRecipes.map((recipe) => (
                                    <RecipeCard key={recipe.slug} recipe={recipe} />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 bg-white rounded-lg">
                                <p className="text-[#1E1E1E]/60">No recipes found for this country yet.</p>
                            </div>
                        )}
                    </>
                ) : continent ? (
                    /* Continent Countries View */
                    <>
                        <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Countries in {selectedContinent}
                        </h2>

                        {countries.length > 0 ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-12">
                                {countries.map((c) => (
                                    <Link
                                        key={c.slug}
                                        to={`/explore/${continent}/${c.slug}`}
                                        className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow flex items-center gap-3"
                                    >
                                        <Globe className="h-8 w-8 text-[#6A1F2E]" />
                                        <div>
                                            <h3 className="font-semibold text-[#1E1E1E]">{c.name}</h3>
                                            <p className="text-sm text-[#1E1E1E]/60">{c.recipe_count} recipes</p>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12 bg-white rounded-lg">
                                <p className="text-[#1E1E1E]/60">No countries with recipes in this continent yet.</p>
                            </div>
                        )}

                        {/* Other Continents */}
                        <div className="mt-12">
                            <h3 className="text-lg font-semibold mb-4">Other Continents</h3>
                            <div className="flex flex-wrap gap-2">
                                {continents.filter(c => c.slug !== continent).map((c) => (
                                    <Button
                                        key={c.slug}
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleContinentSelect(c.slug)}
                                    >
                                        {CONTINENT_INFO[c.name]?.emoji} {c.name}
                                    </Button>
                                ))}
                            </div>
                        </div>
                    </>
                ) : (
                    /* Main Explore View */
                    <>
                        {/* Top 10 Worldwide */}
                        <div className="mb-16">
                            <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                🌍 Top 10 Worldwide
                            </h2>
                            
                            {topRecipes.length > 0 ? (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                    {topRecipes.slice(0, 9).map((recipe, index) => (
                                        <div key={recipe.slug} className="relative">
                                            <Badge className="absolute top-2 left-2 z-10 bg-[#6A1F2E] text-white">
                                                #{index + 1}
                                            </Badge>
                                            <RecipeCard recipe={recipe} />
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 bg-white rounded-lg">
                                    <p className="text-[#1E1E1E]/60">No recipes available yet.</p>
                                </div>
                            )}
                        </div>

                        {/* Continent Selector */}
                        <div>
                            <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                Browse by Continent
                            </h2>
                            
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                                {continents.map((c) => (
                                    <button
                                        key={c.slug}
                                        onClick={() => handleContinentSelect(c.slug)}
                                        className="bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 text-center group"
                                    >
                                        <span className="text-4xl mb-3 block">
                                            {CONTINENT_INFO[c.name]?.emoji || '🌍'}
                                        </span>
                                        <h3 className="font-semibold text-[#1E1E1E] group-hover:text-[#6A1F2E] transition-colors">
                                            {c.name}
                                        </h3>
                                        <p className="text-sm text-[#1E1E1E]/60 mt-1">
                                            {c.recipe_count} recipes
                                        </p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </>
                )}
            </section>
        </div>
    );
};

export default ExplorePage;
