import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Link, useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { recipeAPI, continentAPI, translationAPI } from '@/utils/api';
import { RecipeCard } from '@/components/recipe/RecipeCard';
import { TranslatedRecipeCard } from '@/components/recipe/TranslatedRecipeCard';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { 
    ChefHat, Globe, MapPin, ChevronRight, Home, Star, 
    Filter, X, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';
import { ExploreSEO } from '@/components/seo/SEOHelmet';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

// Dish types for filtering
const DISH_TYPES = [
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
    { value: 'europe', label: 'Europe' },
    { value: 'asia', label: 'Asia' },
    { value: 'americas', label: 'Americas' },
    { value: 'africa', label: 'Africa' },
    { value: 'middle-east', label: 'Middle East' },
    { value: 'oceania', label: 'Oceania' },
];

// Breadcrumb component
const Breadcrumb = ({ continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, t }) => (
    <nav className="flex items-center gap-2 text-xs text-[#5C5C5C] mb-3" aria-label="Breadcrumb">
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
    <div className="bg-white border border-[#E8E4DC] p-4 sticky top-20">
        <h3 className="text-sm font-medium text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
            Highest Rated for Tradition
        </h3>
        <div className="space-y-2">
            {recipes.slice(0, 8).map((recipe, index) => (
                <Link 
                    key={recipe.slug}
                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                    className="flex items-start gap-2 group py-1"
                >
                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-[#6A1F2E] text-white text-[10px] flex items-center justify-center font-medium">
                        {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                        <p className="text-xs text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors line-clamp-2 leading-tight">
                            {recipe.recipe_name || recipe.title_original}
                        </p>
                        <div className="flex items-center gap-1 mt-0.5">
                            <Star className="h-2.5 w-2.5 fill-[#CBA55B] text-[#CBA55B]" />
                            <span className="text-[10px] text-[#7C7C7C]">
                                {recipe.average_rating?.toFixed(1) || '4.5'}
                            </span>
                        </div>
                    </div>
                </Link>
            ))}
        </div>
    </div>
);

// Filter Popover with Checkboxes
const FilterPopover = ({ title, options, selectedValues, onChange, icon: Icon }) => {
    const selectedCount = selectedValues.length;
    
    return (
        <Popover>
            <PopoverTrigger asChild>
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-[#E8E4DC] bg-white hover:border-[#6A1F2E] transition-colors">
                    {Icon && <Icon className="h-3 w-3 text-[#6A1F2E]" />}
                    <span className="text-[#2C2C2C]">{title}</span>
                    {selectedCount > 0 && (
                        <Badge className="bg-[#6A1F2E] text-white text-[10px] px-1.5 py-0 h-4 min-w-4">
                            {selectedCount}
                        </Badge>
                    )}
                    <ChevronDown className="h-3 w-3 text-[#7C7C7C]" />
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-0" align="start">
                <ScrollArea className="h-64">
                    <div className="p-3 space-y-2">
                        {options.map((option) => (
                            <label 
                                key={option.value}
                                className="flex items-center gap-2 cursor-pointer hover:bg-[#F5F2EC] p-1.5 rounded transition-colors"
                            >
                                <Checkbox 
                                    checked={selectedValues.includes(option.value)}
                                    onCheckedChange={(checked) => {
                                        if (checked) {
                                            onChange([...selectedValues, option.value]);
                                        } else {
                                            onChange(selectedValues.filter(v => v !== option.value));
                                        }
                                    }}
                                    className="h-4 w-4 border-[#E8E4DC] data-[state=checked]:bg-[#6A1F2E] data-[state=checked]:border-[#6A1F2E]"
                                />
                                <span className="text-xs text-[#2C2C2C]">{option.label}</span>
                            </label>
                        ))}
                    </div>
                </ScrollArea>
                {selectedCount > 0 && (
                    <div className="border-t border-[#E8E4DC] p-2">
                        <button 
                            onClick={() => onChange([])}
                            className="text-xs text-[#6A1F2E] hover:underline w-full text-left"
                        >
                            Clear {title.toLowerCase()}
                        </button>
                    </div>
                )}
            </PopoverContent>
        </Popover>
    );
};

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
    
    // Filter states - now arrays for multi-select
    const [selectedDishTypes, setSelectedDishTypes] = useState(() => {
        const param = searchParams.get('dishType');
        return param ? param.split(',') : [];
    });
    const [selectedContinents, setSelectedContinents] = useState(() => {
        return continent ? [continent] : [];
    });
    
    // Sync URL params with filter state
    useEffect(() => {
        const dishType = searchParams.get('dishType');
        if (dishType) {
            setSelectedDishTypes(dishType.split(','));
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
            setSelectedContinents([continent]);
        } else {
            loadExploreData();
        }
    }, [continent, country, loadCountryData, loadContinentData, loadExploreData]);

    // Handle dish type filter changes
    const handleDishTypeChange = (values) => {
        setSelectedDishTypes(values);
        if (values.length === 0) {
            searchParams.delete('dishType');
        } else {
            searchParams.set('dishType', values.join(','));
        }
        setSearchParams(searchParams);
    };

    // Handle continent filter changes
    const handleContinentChange = (values) => {
        setSelectedContinents(values);
        if (values.length === 1) {
            navigate(getLocalizedPath(`/explore/${values[0]}`));
        } else if (values.length === 0) {
            navigate(getLocalizedPath('/explore'));
        }
    };

    const handleContinentSelect = useCallback((continentSlug) => {
        navigate(getLocalizedPath(`/explore/${continentSlug}`));
    }, [navigate, getLocalizedPath]);

    // Clear all filters
    const clearAllFilters = () => {
        setSelectedDishTypes([]);
        setSelectedContinents([]);
        searchParams.delete('dishType');
        setSearchParams(searchParams);
        navigate(getLocalizedPath('/explore'));
    };

    // Active filters count
    const activeFiltersCount = selectedDishTypes.length + selectedContinents.length;

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
            <section className="bg-white border-b border-[#E8E4DC] py-6 px-4">
                <div className="max-w-6xl mx-auto">
                    <Breadcrumb {...breadcrumbProps} />
                    <h1 className="text-2xl sm:text-3xl font-light text-[#2C2C2C]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                        {country ? translateName(pageTitle, 'countries') : 
                         continent ? translateName(pageTitle, 'continents') : 
                         'Explore Recipes'}
                    </h1>
                </div>
            </section>

            {/* TOP FILTER BAR */}
            <section className="bg-[#F9F7F3] border-b border-[#E8E4DC] py-3 px-4 sticky top-16 z-40">
                <div className="max-w-6xl mx-auto">
                    <div className="flex items-center gap-3 flex-wrap">
                        {/* Filter Label */}
                        <span className="text-xs text-[#7C7C7C] uppercase tracking-wide hidden sm:inline">Filters:</span>
                        
                        {/* Dish Type Filter */}
                        <FilterPopover 
                            title="Dish Type"
                            options={DISH_TYPES}
                            selectedValues={selectedDishTypes}
                            onChange={handleDishTypeChange}
                            icon={ChefHat}
                        />
                        
                        {/* Continent Filter */}
                        <FilterPopover 
                            title="Continent"
                            options={CONTINENTS}
                            selectedValues={selectedContinents}
                            onChange={handleContinentChange}
                            icon={Globe}
                        />
                        
                        {/* Active Filter Tags */}
                        {activeFiltersCount > 0 && (
                            <>
                                <div className="h-4 w-px bg-[#E8E4DC] mx-1 hidden sm:block"></div>
                                
                                {selectedDishTypes.map(dt => (
                                    <Badge 
                                        key={dt}
                                        variant="secondary" 
                                        className="bg-[#6A1F2E]/10 text-[#6A1F2E] text-[10px] px-2 py-0.5 gap-1"
                                    >
                                        {DISH_TYPES.find(d => d.value === dt)?.label}
                                        <button onClick={() => handleDishTypeChange(selectedDishTypes.filter(v => v !== dt))}>
                                            <X className="h-2.5 w-2.5" />
                                        </button>
                                    </Badge>
                                ))}
                                
                                {selectedContinents.map(c => (
                                    <Badge 
                                        key={c}
                                        variant="secondary" 
                                        className="bg-[#6A1F2E]/10 text-[#6A1F2E] text-[10px] px-2 py-0.5 gap-1"
                                    >
                                        {CONTINENTS.find(cont => cont.value === c)?.label}
                                        <button onClick={() => handleContinentChange(selectedContinents.filter(v => v !== c))}>
                                            <X className="h-2.5 w-2.5" />
                                        </button>
                                    </Badge>
                                ))}
                                
                                <button 
                                    onClick={clearAllFilters}
                                    className="text-[10px] text-[#6A1F2E] hover:underline ml-1"
                                >
                                    Clear all
                                </button>
                            </>
                        )}
                        
                        {/* Recipe Count */}
                        <span className="text-xs text-[#7C7C7C] ml-auto">
                            {allRecipes.length} recipes
                        </span>
                    </div>
                </div>
            </section>

            {/* Main Content */}
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="flex gap-6">
                    
                    {/* CENTER: Main Content */}
                    <main className="flex-1 min-w-0">
                        {loading ? (
                            <div className="text-center py-12">
                                <ChefHat className="h-8 w-8 mx-auto text-[#6A1F2E] animate-pulse mb-3" />
                                <p className="text-sm text-[#7C7C7C] font-light">Loading recipes...</p>
                            </div>
                        ) : country ? (
                            /* Country Recipes View */
                            <>
                                <div className="flex items-center gap-2 mb-4 text-xs text-[#5C5C5C]">
                                    <MapPin className="h-3 w-3 text-[#6A1F2E]" />
                                    <span>{countryRecipes.length} recipes from {translateName(pageTitle, 'countries')}</span>
                                </div>

                                {countryRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {countryRecipes.map((recipe) => (
                                            <TranslatedRecipeCard key={recipe.slug} recipe={recipe} />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]">
                                        <p className="text-sm text-[#7C7C7C] font-light">No recipes found</p>
                                    </div>
                                )}
                            </>
                        ) : continent ? (
                            /* Continent Countries View */
                            <>
                                <h2 className="text-lg font-light mb-4 text-[#2C2C2C]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    Countries in {translateName(selectedContinent, 'continents')}
                                </h2>

                                {countries.length > 0 ? (
                                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
                                        {countries.map((c) => (
                                            <Link
                                                key={c.slug}
                                                to={getLocalizedPath(`/explore/${continent}/${c.slug}`)}
                                                className="bg-white border border-[#E8E4DC] p-3 hover:border-[#6A1F2E] transition-colors flex items-center gap-2"
                                            >
                                                <Globe className="h-4 w-4 text-[#6A1F2E]" />
                                                <div>
                                                    <h3 className="font-medium text-[#2C2C2C] text-sm">{translateName(c.name, 'countries')}</h3>
                                                    <p className="text-[10px] text-[#7C7C7C]">{c.recipe_count} recipes</p>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]">
                                        <p className="text-sm text-[#7C7C7C] font-light">No countries found</p>
                                    </div>
                                )}

                                {/* Other Continents */}
                                <div className="pt-6 border-t border-[#E8E4DC]">
                                    <h3 className="text-xs font-medium text-[#5C5C5C] mb-2 uppercase tracking-wide">Other Continents</h3>
                                    <div className="flex flex-wrap gap-2">
                                        {continents.filter(c => c.slug !== continent).map((c) => (
                                            <Button
                                                key={c.slug}
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="border-[#E8E4DC] text-[#2C2C2C] hover:border-[#6A1F2E] hover:text-[#6A1F2E] text-xs h-7 px-3"
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
                                {allRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {allRecipes.map((recipe) => (
                                            <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]">
                                        <p className="text-sm text-[#7C7C7C] font-light">No recipes found</p>
                                    </div>
                                )}

                                {/* Continent Quick Links */}
                                <div className="mt-10 pt-6 border-t border-[#E8E4DC]">
                                    <h3 className="text-base font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        Browse by Continent
                                    </h3>
                                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                        {continents.map((c) => (
                                            <button
                                                key={c.slug}
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="bg-white border border-[#E8E4DC] p-3 hover:border-[#6A1F2E] transition-colors text-center group"
                                            >
                                                <h4 className="font-medium text-[#2C2C2C] group-hover:text-[#6A1F2E] transition-colors text-xs">
                                                    {translateName(c.name, 'continents')}
                                                </h4>
                                                <p className="text-[10px] text-[#7C7C7C] mt-0.5">
                                                    {c.recipe_count}
                                                </p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </main>

                    {/* RIGHT: Ranking Sidebar (Desktop only) */}
                    <aside className="hidden lg:block w-56 flex-shrink-0">
                        <RankingSidebar recipes={topRecipes} getLocalizedPath={getLocalizedPath} />
                    </aside>
                </div>

                {/* Mobile Rankings (below content) */}
                <div className="lg:hidden mt-8">
                    <div className="bg-white border border-[#E8E4DC] p-4">
                        <h3 className="text-sm font-medium text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            Highest Rated for Tradition
                        </h3>
                        <div className="grid grid-cols-2 gap-2">
                            {topRecipes.slice(0, 6).map((recipe, index) => (
                                <Link 
                                    key={recipe.slug}
                                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                                    className="flex items-start gap-2 p-2 bg-[#FDFBF7] hover:bg-[#F5F2EC] transition-colors"
                                >
                                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-[#6A1F2E] text-white text-[10px] flex items-center justify-center font-medium">
                                        {index + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-[#2C2C2C] line-clamp-2">
                                            {recipe.recipe_name || recipe.title_original}
                                        </p>
                                        <div className="flex items-center gap-1 mt-0.5">
                                            <Star className="h-2.5 w-2.5 fill-[#CBA55B] text-[#CBA55B]" />
                                            <span className="text-[10px] text-[#7C7C7C]">
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
