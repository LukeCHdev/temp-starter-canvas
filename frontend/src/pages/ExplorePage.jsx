import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Link, useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI, continentAPI, translationAPI } from '@/utils/api';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { TranslatedRecipeCard } from '@/components/recipe/TranslatedRecipeCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
    ChefHat, Globe, MapPin, ChevronRight, Home, Star, 
    Filter, X, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';
import { ExploreSEO } from '@/components/seo/SEOHelmet';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

// Dish types for filtering
const DISH_TYPES = [
    { value: 'all', label: 'All Dish Types' },
    { value: 'appetizer', label: 'Appetizers' },
    { value: 'aperitif', label: 'Aperitif & Small Plates' },
    { value: 'first-course', label: 'First Courses' },
    { value: 'main-course', label: 'Main Courses' },
    { value: 'side-dish', label: 'Side Dishes' },
    { value: 'dessert', label: 'Desserts' },
    { value: 'street-food', label: 'Street Food' },
    { value: 'festive', label: 'Festive & Ritual Dishes' },
];

// Continent options
const CONTINENTS = [
    { value: 'all', label: 'All Continents', slug: '' },
    { value: 'europe', label: 'Europe', slug: 'europe' },
    { value: 'asia', label: 'Asia', slug: 'asia' },
    { value: 'americas', label: 'Americas', slug: 'americas' },
    { value: 'africa', label: 'Africa', slug: 'africa' },
    { value: 'middle-east', label: 'Middle East', slug: 'middle-east' },
    { value: 'oceania', label: 'Oceania', slug: 'oceania' },
];

// Breadcrumb component
const Breadcrumb = ({ continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, t }) => (
    <nav className="flex items-center gap-2 text-sm text-[#5C5C5C] mb-4" aria-label="Breadcrumb">
        <Link to={getLocalizedPath('/')} className="hover:text-[#6A1F2E] flex items-center gap-1">
            <Home className="h-3 w-3" />
            Home
        </Link>
        <ChevronRight className="h-3 w-3" />
        <Link to={getLocalizedPath('/explore')} className={`hover:text-[#6A1F2E] ${!continent ? 'text-[#6A1F2E] font-medium' : ''}`}>
            Explore
        </Link>
        {continent && (
            <>
                <ChevronRight className="h-3 w-3" />
                <Link 
                    to={getLocalizedPath(`/explore/${continent}`)} 
                    className={`hover:text-[#6A1F2E] ${!country ? 'text-[#6A1F2E] font-medium' : ''}`}
                >
                    {translateName(selectedContinent || continent.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()), 'continents')}
                </Link>
            </>
        )}
        {country && (
            <>
                <ChevronRight className="h-3 w-3" />
                <span className="text-[#6A1F2E] font-medium">
                    {translateName(pageTitle, 'countries')}
                </span>
            </>
        )}
    </nav>
);

// Ranking Sidebar Component
const RankingSidebar = ({ recipes, getLocalizedPath }) => (
    <div className="bg-white border border-[#E8E4DC] p-5 sticky top-24">
        <h3 className="text-base font-medium text-[#2C2C2C] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
            Highest Rated for Tradition
        </h3>
        <div className="space-y-3">
            {recipes.slice(0, 8).map((recipe, index) => (
                <Link 
                    key={recipe.slug}
                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                    className="flex items-start gap-3 group"
                >
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#6A1F2E] text-white text-xs flex items-center justify-center font-medium">
                        {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors line-clamp-2 leading-tight">
                            {recipe.recipe_name || recipe.title_original}
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                            <Star className="h-3 w-3 fill-[#CBA55B] text-[#CBA55B]" />
                            <span className="text-xs text-[#7C7C7C]">
                                {recipe.average_rating?.toFixed(1) || '4.5'}
                            </span>
                            <span className="text-xs text-[#9C9C9C]">·</span>
                            <span className="text-xs text-[#9C9C9C]">
                                {recipe.origin_country}
                            </span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    </div>
);

// Mobile Filter Button
const MobileFilterButton = ({ activeFilters, onClick }) => (
    <button 
        onClick={onClick}
        className="md:hidden flex items-center gap-2 px-4 py-2 border border-[#E8E4DC] bg-white text-sm text-[#2C2C2C]"
    >
        <Filter className="h-4 w-4" />
        Refine
        {activeFilters > 0 && (
            <Badge className="bg-[#6A1F2E] text-white text-xs px-1.5 py-0">
                {activeFilters}
            </Badge>
        )}
    </button>
);

const ExplorePage = () => {
    const { continent, country } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const [searchParams, setSearchParams] = useSearchParams();
    const { t, i18n } = useTranslation();
    const { language, getLocalizedPath } = useLanguage();
    
    const [topRecipes, setTopRecipes] = useState([]);
    const [allRecipes, setAllRecipes] = useState([]);
    const [continents, setContinents] = useState([]);
    const [countries, setCountries] = useState([]);
    const [countryRecipes, setCountryRecipes] = useState([]);
    const [selectedContinent, setSelectedContinent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [pageTitle, setPageTitle] = useState('Explore');
    const [showMobileFilters, setShowMobileFilters] = useState(false);
    
    // Filter states
    const [dishTypeFilter, setDishTypeFilter] = useState(searchParams.get('dishType') || 'all');
    const [continentFilter, setContinentFilter] = useState(continent || 'all');
    
    // Sync URL params with filter state
    useEffect(() => {
        const dishType = searchParams.get('dishType');
        if (dishType) {
            setDishTypeFilter(dishType);
        }
    }, [searchParams]);
    
    // Language sync
    useEffect(() => {
        const pathSegments = location.pathname.split('/').filter(Boolean);
        const urlLang = pathSegments[0];
        if (SUPPORTED_LANGUAGES[urlLang] && urlLang !== i18n.language) {
            i18n.changeLanguage(urlLang);
        }
    }, [location.pathname, i18n]);
    
    // Translate helper
    const translateName = useCallback((name, type = 'countries') => {
        const key = `${type}.${name}`;
        const translated = t(key, { defaultValue: name });
        return translated === key ? name : translated;
    }, [t]);

    // Load explore data
    const loadExploreData = useCallback(async () => {
        setLoading(true);
        try {
            const [topRes, continentRes, allRes] = await Promise.all([
                recipeAPI.getTopWorldwide(10, language),
                continentAPI.getAll(),
                recipeAPI.getAll({ limit: 50, lang: language })
            ]);
            
            setTopRecipes(topRes.data.recipes || []);
            setContinents(continentRes.data.continents || []);
            setAllRecipes(allRes.data.recipes || allRes.data || []);
            setPageTitle('Explore');
            setSelectedContinent(null);
            setCountries([]);
            setCountryRecipes([]);
        } catch (error) {
            console.error('Error loading explore data:', error);
            toast.error('Failed to load data');
        } finally {
            setLoading(false);
        }
    }, [language]);

    // Load continent data
    const loadContinentData = useCallback(async (continentSlug) => {
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
    }, []);

    // Load country data
    const loadCountryData = useCallback(async (countrySlug, continentSlug) => {
        setLoading(true);
        const currentLang = language || 'en';
        
        try {
            const res = await translationAPI.getRecipes({
                country: countrySlug.replace('-', ' '),
                lang: currentLang,
                limit: 100
            });
            
            setCountryRecipes(res.data.recipes || []);
            
            const firstRecipe = res.data.recipes?.[0];
            const countryName = firstRecipe?.metadata?.origin_country || countrySlug.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
            const continentName = firstRecipe?.metadata?.origin_region || continentSlug?.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            setSelectedContinent(continentName);
            setPageTitle(countryName);
        } catch (error) {
            console.error('Error loading country data:', error);
            try {
                const fallbackRes = await recipeAPI.getByCountryName(countrySlug);
                setCountryRecipes(fallbackRes.data.recipes || []);
                setSelectedContinent(fallbackRes.data.continent);
                setPageTitle(fallbackRes.data.country);
            } catch (fallbackError) {
                toast.error('Failed to load recipes');
            }
        } finally {
            setLoading(false);
        }
    }, [language]);

    // Main effect
    useEffect(() => {
        if (country) {
            loadCountryData(country, continent);
        } else if (continent) {
            loadContinentData(continent);
            setContinentFilter(continent);
        } else {
            loadExploreData();
        }
    }, [continent, country, loadCountryData, loadContinentData, loadExploreData]);

    // Handle filter changes
    const handleDishTypeChange = (value) => {
        setDishTypeFilter(value);
        if (value === 'all') {
            searchParams.delete('dishType');
        } else {
            searchParams.set('dishType', value);
        }
        setSearchParams(searchParams);
    };

    const handleContinentChange = (value) => {
        setContinentFilter(value);
        if (value === 'all') {
            navigate(getLocalizedPath('/explore'));
        } else {
            navigate(getLocalizedPath(`/explore/${value}`));
        }
    };

    const handleContinentSelect = useCallback((continentSlug) => {
        navigate(getLocalizedPath(`/explore/${continentSlug}`));
    }, [navigate, getLocalizedPath]);

    // Clear all filters
    const clearFilters = () => {
        setDishTypeFilter('all');
        setContinentFilter('all');
        searchParams.delete('dishType');
        setSearchParams(searchParams);
        navigate(getLocalizedPath('/explore'));
    };

    // Active filters count
    const activeFiltersCount = (dishTypeFilter !== 'all' ? 1 : 0) + (continentFilter !== 'all' ? 1 : 0);

    // Breadcrumb props
    const breadcrumbProps = useMemo(() => ({
        continent,
        country,
        selectedContinent,
        pageTitle,
        getLocalizedPath,
        translateName,
        t
    }), [continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, t]);

    // SEO path
    const seoPath = useMemo(() => {
        if (country) return `/explore/${continent}/${country}`;
        if (continent) return `/explore/${continent}`;
        return '/explore';
    }, [continent, country]);

    // SEO breadcrumbs
    const seoBreadcrumbs = useMemo(() => {
        const crumbs = [
            { name: 'Home', path: '/' },
            { name: 'Explore', path: '/explore' }
        ];
        if (continent && selectedContinent) {
            crumbs.push({ name: selectedContinent, path: `/explore/${continent}` });
        }
        if (country && pageTitle) {
            crumbs.push({ name: pageTitle, path: `/explore/${continent}/${country}` });
        }
        return crumbs;
    }, [continent, country, selectedContinent, pageTitle]);

    return (
        <div className="min-h-screen bg-[#FDFBF7]" data-testid="explore-page">
            {/* SEO Metadata */}
            <ExploreSEO 
                continent={selectedContinent}
                country={pageTitle}
                path={seoPath}
                breadcrumbs={seoBreadcrumbs}
            />
            
            {/* Header */}
            <section className="bg-white border-b border-[#E8E4DC] py-8 px-4">
                <div className="max-w-7xl mx-auto">
                    <Breadcrumb {...breadcrumbProps} />
                    <h1 className="text-3xl sm:text-4xl font-light text-[#2C2C2C]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {country ? translateName(pageTitle, 'countries') : 
                         continent ? translateName(pageTitle, 'continents') : 
                         'Explore Recipes'}
                    </h1>
                    {!country && !continent && (
                        <p className="text-[#5C5C5C] mt-2 font-light">
                            Discover authentic recipes from around the world
                        </p>
                    )}
                </div>
            </section>

            {/* Main Content - 3 Column Layout */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="flex flex-col lg:flex-row gap-8">
                    
                    {/* LEFT: Filters */}
                    <aside className={`lg:w-56 flex-shrink-0 ${showMobileFilters ? 'block' : 'hidden lg:block'}`}>
                        <div className="bg-white border border-[#E8E4DC] p-5 sticky top-24">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-sm font-medium text-[#2C2C2C] uppercase tracking-wide">
                                    Filters
                                </h3>
                                {activeFiltersCount > 0 && (
                                    <button 
                                        onClick={clearFilters}
                                        className="text-xs text-[#6A1F2E] hover:underline"
                                    >
                                        Clear all
                                    </button>
                                )}
                            </div>
                            
                            {/* Dish Type Filter */}
                            <div className="mb-5">
                                <label className="block text-xs text-[#7C7C7C] mb-2 uppercase tracking-wide">
                                    Dish Type
                                </label>
                                <Select value={dishTypeFilter} onValueChange={handleDishTypeChange}>
                                    <SelectTrigger className="w-full border-[#E8E4DC] text-sm">
                                        <SelectValue placeholder="All Dish Types" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {DISH_TYPES.map((type) => (
                                            <SelectItem key={type.value} value={type.value}>
                                                {type.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            
                            {/* Continent Filter */}
                            <div className="mb-5">
                                <label className="block text-xs text-[#7C7C7C] mb-2 uppercase tracking-wide">
                                    Continent
                                </label>
                                <Select value={continentFilter} onValueChange={handleContinentChange}>
                                    <SelectTrigger className="w-full border-[#E8E4DC] text-sm">
                                        <SelectValue placeholder="All Continents" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {CONTINENTS.map((c) => (
                                            <SelectItem key={c.value} value={c.value}>
                                                {c.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            
                            {/* Active Filters Display */}
                            {activeFiltersCount > 0 && (
                                <div className="pt-4 border-t border-[#E8E4DC]">
                                    <p className="text-xs text-[#7C7C7C] mb-2">Active filters:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {dishTypeFilter !== 'all' && (
                                            <Badge variant="secondary" className="bg-[#F5F2EC] text-[#2C2C2C] text-xs">
                                                {DISH_TYPES.find(d => d.value === dishTypeFilter)?.label}
                                                <button onClick={() => handleDishTypeChange('all')} className="ml-1">
                                                    <X className="h-3 w-3" />
                                                </button>
                                            </Badge>
                                        )}
                                        {continentFilter !== 'all' && (
                                            <Badge variant="secondary" className="bg-[#F5F2EC] text-[#2C2C2C] text-xs">
                                                {CONTINENTS.find(c => c.value === continentFilter)?.label}
                                                <button onClick={() => handleContinentChange('all')} className="ml-1">
                                                    <X className="h-3 w-3" />
                                                </button>
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </aside>

                    {/* CENTER: Main Content */}
                    <main className="flex-1 min-w-0">
                        {/* Mobile Filter Button */}
                        <div className="lg:hidden mb-4">
                            <MobileFilterButton 
                                activeFilters={activeFiltersCount} 
                                onClick={() => setShowMobileFilters(!showMobileFilters)} 
                            />
                        </div>

                        {loading ? (
                            <div className="text-center py-16">
                                <ChefHat className="h-10 w-10 mx-auto text-[#6A1F2E] animate-pulse mb-4" />
                                <p className="text-[#7C7C7C] font-light">Loading recipes...</p>
                            </div>
                        ) : country ? (
                            /* Country Recipes View */
                            <>
                                <div className="flex items-center gap-2 mb-6 text-sm text-[#5C5C5C]">
                                    <MapPin className="h-4 w-4 text-[#6A1F2E]" />
                                    <span>{countryRecipes.length} recipes from {translateName(pageTitle, 'countries')}</span>
                                </div>

                                {countryRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                        {countryRecipes.map((recipe) => (
                                            <TranslatedRecipeCard key={recipe.slug} recipe={recipe} />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-16 bg-white border border-[#E8E4DC]">
                                        <p className="text-[#7C7C7C] font-light">No recipes found</p>
                                    </div>
                                )}
                            </>
                        ) : continent ? (
                            /* Continent Countries View */
                            <>
                                <h2 className="text-xl font-light mb-6 text-[#2C2C2C]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    Countries in {translateName(selectedContinent, 'continents')}
                                </h2>

                                {countries.length > 0 ? (
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
                                        {countries.map((c) => (
                                            <Link
                                                key={c.slug}
                                                to={getLocalizedPath(`/explore/${continent}/${c.slug}`)}
                                                className="bg-white border border-[#E8E4DC] p-4 hover:border-[#6A1F2E] transition-colors flex items-center gap-3"
                                            >
                                                <Globe className="h-6 w-6 text-[#6A1F2E]" />
                                                <div>
                                                    <h3 className="font-medium text-[#2C2C2C] text-sm">{translateName(c.name, 'countries')}</h3>
                                                    <p className="text-xs text-[#7C7C7C]">{c.recipe_count} recipes</p>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-16 bg-white border border-[#E8E4DC]">
                                        <p className="text-[#7C7C7C] font-light">No countries found</p>
                                    </div>
                                )}

                                {/* Other Continents */}
                                <div className="mt-10 pt-6 border-t border-[#E8E4DC]">
                                    <h3 className="text-sm font-medium text-[#5C5C5C] mb-3 uppercase tracking-wide">Other Continents</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {continents.filter(c => c.slug !== continent).map((c) => (
                                            <Button
                                                key={c.slug}
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="border-[#E8E4DC] text-[#2C2C2C] hover:border-[#6A1F2E] hover:text-[#6A1F2E] text-xs"
                                            >
                                                {c.name}
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            /* Main Explore View - Recipe Grid */
                            <>
                                <div className="flex items-center justify-between mb-6">
                                    <p className="text-sm text-[#5C5C5C]">
                                        {allRecipes.length} authentic recipes
                                    </p>
                                </div>

                                {allRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                        {allRecipes.map((recipe) => (
                                            <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-16 bg-white border border-[#E8E4DC]">
                                        <p className="text-[#7C7C7C] font-light">No recipes found</p>
                                    </div>
                                )}

                                {/* Continent Quick Links */}
                                <div className="mt-12 pt-8 border-t border-[#E8E4DC]">
                                    <h3 className="text-lg font-light text-[#2C2C2C] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        Browse by Continent
                                    </h3>
                                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                                        {continents.map((c) => (
                                            <button
                                                key={c.slug}
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="bg-white border border-[#E8E4DC] p-4 hover:border-[#6A1F2E] transition-colors text-center group"
                                            >
                                                <h4 className="font-medium text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors text-sm">
                                                    {translateName(c.name, 'continents')}
                                                </h4>
                                                <p className="text-xs text-[#7C7C7C] mt-1">
                                                    {c.recipe_count} recipes
                                                </p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </main>

                    {/* RIGHT: Ranking Sidebar */}
                    <aside className="hidden lg:block w-64 flex-shrink-0">
                        <RankingSidebar recipes={topRecipes} getLocalizedPath={getLocalizedPath} />
                    </aside>
                </div>

                {/* Mobile Rankings (below content) */}
                <div className="lg:hidden mt-10">
                    <div className="bg-white border border-[#E8E4DC] p-5">
                        <h3 className="text-base font-medium text-[#2C2C2C] mb-4" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Highest Rated for Tradition
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {topRecipes.slice(0, 6).map((recipe, index) => (
                                <Link 
                                    key={recipe.slug}
                                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                                    className="flex items-start gap-3 p-3 bg-[#FDFBF7] hover:bg-[#F5F2EC] transition-colors"
                                >
                                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[#6A1F2E] text-white text-xs flex items-center justify-center font-medium">
                                        {index + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-[#2C2C2C] line-clamp-2">
                                            {recipe.recipe_name || recipe.title_original}
                                        </p>
                                        <div className="flex items-center gap-1 mt-1">
                                            <Star className="h-3 w-3 fill-[#CBA55B] text-[#CBA55B]" />
                                            <span className="text-xs text-[#7C7C7C]">
                                                {recipe.average_rating?.toFixed(1) || '4.5'}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ExplorePage;
