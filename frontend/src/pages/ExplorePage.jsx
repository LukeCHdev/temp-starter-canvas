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
    Filter, X, ChevronDown, Search
} from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage, SUPPORTED_LANGUAGES } from '@/context/LanguageContext';
import { ExploreSEO } from '@/components/seo/SEOHelmet';
import { t as translate } from '@/i18n/translations';
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";

// Dish types for filtering - keys for translation lookup
const DISH_TYPE_KEYS = [
    { value: 'appetizer', key: 'appetizer' },
    { value: 'aperitif', key: 'aperitif' },
    { value: 'first-course', key: 'firstCourse' },
    { value: 'main-course', key: 'mainCourse' },
    { value: 'side-dish', key: 'sideDish' },
    { value: 'dessert', key: 'dessert' },
    { value: 'street-food', key: 'streetFood' },
    { value: 'festive', key: 'festive' },
];

// Continent options - keys for translation lookup
const CONTINENT_KEYS = [
    { value: 'Europe', key: 'Europe' },
    { value: 'Asia', key: 'Asia' },
    { value: 'Americas', key: 'Americas' },
    { value: 'Africa', key: 'Africa' },
    { value: 'Middle East', key: 'Middle East' },
    { value: 'Oceania', key: 'Oceania' },
];

// Breadcrumb component with translations
const Breadcrumb = ({ continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, lang }) => (
    <nav className="flex items-center gap-2 text-xs text-[#5C5C5C] mb-3" aria-label="Breadcrumb">
        <Link to={getLocalizedPath('/')} className="hover:text-[#6A1F2E] flex items-center gap-1">
            <Home className="h-3 w-3" />
            {translate('common.home', lang)}
        </Link>
        <ChevronRight className="h-3 w-3" />
        <Link to={getLocalizedPath('/explore')} className={`hover:text-[#6A1F2E] ${!continent ? 'text-[#6A1F2E] font-medium' : ''}`}>
            {translate('nav.explore', lang)}
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

// Ranking Sidebar Component with translations
const RankingSidebar = ({ recipes, getLocalizedPath, lang }) => (
    <div className="bg-white border border-[#E8E4DC] p-4 sticky top-20">
        <h3 className="text-sm font-medium text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
            {translate('explore.highestRated', lang)}
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

// Filter Popover with Checkboxes and translations
const FilterPopover = ({ title, options, selectedValues, onChange, icon: Icon, lang, clearLabel }) => {
    const selectedCount = selectedValues.length;
    
    return (
        <Popover>
            <PopoverTrigger asChild>
                <button 
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-[#E8E4DC] bg-white hover:border-[#6A1F2E] transition-colors"
                    data-testid={`filter-${title.toLowerCase().replace(/\s+/g, '-')}`}
                >
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
                                data-testid={`filter-option-${option.value}`}
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
                            {clearLabel}
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
    const lang = language || 'en';
    
    const [topRecipes, setTopRecipes] = useState([]);
    const [allRecipes, setAllRecipes] = useState([]);
    const [continents, setContinents] = useState([]);
    const [countries, setCountries] = useState([]);
    const [countryRecipes, setCountryRecipes] = useState([]);
    const [selectedContinent, setSelectedContinent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [pageTitle, setPageTitle] = useState('Explore');
    
    // Search state
    const [searchText, setSearchText] = useState('');
    
    // Filter states - arrays for multi-select
    const [selectedDishTypes, setSelectedDishTypes] = useState(() => {
        const param = searchParams.get('dishType');
        return param ? param.split(',') : [];
    });
    const [selectedContinents, setSelectedContinents] = useState(() => {
        return continent ? [continent.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())] : [];
    });

    // Get translated dish types
    const dishTypeOptions = useMemo(() => 
        DISH_TYPE_KEYS.map(dt => ({
            value: dt.value,
            label: translate(`homepage.dishTypes.${dt.key}`, lang)
        })), [lang]
    );

    // Get translated continents (use actual continent names as values since DB uses names like "Europe")
    const continentOptions = useMemo(() => 
        CONTINENT_KEYS.map(c => ({
            value: c.value,
            label: translate(`continents.${c.key}`, lang)
        })), [lang]
    );
    
    // Sync URL params with filter state (handles browser back/forward)
    useEffect(() => {
        const dishType = searchParams.get('dishType');
        setSelectedDishTypes(dishType ? dishType.split(',') : []);
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

    // Load explore data - load ALL published recipes for client-side filtering
    const loadExploreData = useCallback(async () => {
        setLoading(true);
        const currentLang = language || 'en';
        
        try {
            const [topRes, recipesRes, continentsRes] = await Promise.all([
                recipeAPI.getTopWorldwide(10, currentLang),
                recipeAPI.getFeatured(300, currentLang, 0),
                continentAPI.getAll()
            ]);
            
            setTopRecipes(topRes.data.recipes || []);
            setAllRecipes(recipesRes.data.recipes || []);
            setContinents(continentsRes.data.continents || []);
            setPageTitle(translate('explore.title', currentLang));
        } catch (error) {
            console.error('Error loading explore data:', error);
            toast.error(translate('search.failed', currentLang));
        } finally {
            setLoading(false);
        }
    }, [language]);

    // Load continent data
    const loadContinentData = useCallback(async (continentSlug) => {
        setLoading(true);
        try {
            const countriesRes = await continentAPI.getCountries(continentSlug);
            setCountries(countriesRes.data.countries || []);
            setSelectedContinent(countriesRes.data.continent);
            setPageTitle(countriesRes.data.continent);
            setCountryRecipes([]);
        } catch (error) {
            console.error('Error loading continent data:', error);
            toast.error(translate('search.failed', lang));
        } finally {
            setLoading(false);
        }
    }, [lang]);

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
                toast.error(translate('search.failed', currentLang));
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
        } else {
            loadExploreData();
        }
    }, [continent, country, loadCountryData, loadContinentData, loadExploreData]);

    // CLIENT-SIDE COMBINED FILTERING: search + dish type + continent
    const filteredRecipes = useMemo(() => {
        let result = allRecipes;

        // Text search filter
        if (searchText.trim()) {
            const query = searchText.trim().toLowerCase();
            result = result.filter(r => {
                const name = (r.recipe_name || r.title_original || '').toLowerCase();
                const country = (r.origin_country || '').toLowerCase();
                const region = (r.origin_region || '').toLowerCase();
                const dishType = (r.dish_type || '').toLowerCase();
                return name.includes(query) || country.includes(query) || region.includes(query) || dishType.includes(query);
            });
        }

        // Dish type filter
        if (selectedDishTypes.length > 0) {
            result = result.filter(r => selectedDishTypes.includes(r.dish_type));
        }

        // Continent filter (use continent name from DB, e.g. "Europe", "Asia")
        if (selectedContinents.length > 0) {
            result = result.filter(r => selectedContinents.includes(r.continent));
        }

        return result;
    }, [allRecipes, searchText, selectedDishTypes, selectedContinents]);

    // Handle dish type filter changes
    const handleDishTypeChange = (values) => {
        setSelectedDishTypes(values);
        const newParams = new URLSearchParams(searchParams);
        if (values.length === 0) {
            newParams.delete('dishType');
        } else {
            newParams.set('dishType', values.join(','));
        }
        setSearchParams(newParams);
    };

    // Handle continent filter changes (client-side only, no navigation)
    const handleContinentChange = (values) => {
        setSelectedContinents(values);
    };

    const handleContinentSelect = useCallback((continentSlug) => {
        navigate(getLocalizedPath(`/explore/${continentSlug}`));
    }, [navigate, getLocalizedPath]);

    // Clear all filters
    const clearAllFilters = () => {
        setSelectedDishTypes([]);
        setSelectedContinents([]);
        setSearchText('');
        const newParams = new URLSearchParams(searchParams);
        newParams.delete('dishType');
        setSearchParams(newParams);
        if (continent) {
            navigate(getLocalizedPath('/explore'));
        }
    };

    // Active filters count
    const activeFiltersCount = selectedDishTypes.length + selectedContinents.length + (searchText.trim() ? 1 : 0);

    // Pagination: show 24 initially, load more in increments
    const RECIPES_PER_PAGE = 24;
    const [visibleCount, setVisibleCount] = useState(RECIPES_PER_PAGE);

    // Reset visible count when filters change
    useEffect(() => {
        setVisibleCount(RECIPES_PER_PAGE);
    }, [searchText, selectedDishTypes, selectedContinents]);

    const visibleRecipes = useMemo(() => 
        filteredRecipes.slice(0, visibleCount), 
        [filteredRecipes, visibleCount]
    );
    const hasMore = visibleCount < filteredRecipes.length;

    // Breadcrumb props
    const breadcrumbProps = useMemo(() => ({
        continent,
        country,
        selectedContinent,
        pageTitle,
        getLocalizedPath,
        translateName,
        lang
    }), [continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, lang]);

    // SEO path
    const seoPath = useMemo(() => {
        if (country) return `/explore/${continent}/${country}`;
        if (continent) return `/explore/${continent}`;
        return '/explore';
    }, [continent, country]);

    // SEO breadcrumbs
    const seoBreadcrumbs = useMemo(() => {
        const crumbs = [
            { name: translate('common.home', lang), path: '/' },
            { name: translate('nav.explore', lang), path: '/explore' }
        ];
        if (continent && selectedContinent) {
            crumbs.push({ name: selectedContinent, path: `/explore/${continent}` });
        }
        if (country && pageTitle) {
            crumbs.push({ name: pageTitle, path: `/explore/${continent}/${country}` });
        }
        return crumbs;
    }, [continent, country, selectedContinent, pageTitle, lang]);

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
                         translate('explore.title', lang)}
                    </h1>
                </div>
            </section>

            {/* TOP FILTER BAR - only show on main explore view (not continent/country sub-views) */}
            {!continent && !country && (
                <section className="bg-[#F9F7F3] border-b border-[#E8E4DC] py-3 px-4 sticky top-16 z-40">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex items-center gap-3 flex-wrap">
                            {/* Search Input */}
                            <div className="relative flex-shrink-0 w-full sm:w-auto sm:min-w-[220px]">
                                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-[#9C9C9C]" />
                                <input
                                    type="text"
                                    value={searchText}
                                    onChange={(e) => setSearchText(e.target.value)}
                                    placeholder={translate('homepage.hero.searchPlaceholder', lang)}
                                    className="w-full pl-8 pr-3 py-1.5 text-xs border border-[#E8E4DC] bg-white focus:border-[#6A1F2E] focus:outline-none focus:ring-1 focus:ring-[#6A1F2E]/20 transition-colors"
                                    data-testid="explore-search-input"
                                />
                            </div>

                            {/* Filter Label */}
                            <span className="text-xs text-[#7C7C7C] uppercase tracking-wide hidden sm:inline">
                                {translate('explore.filters', lang)}:
                            </span>
                            
                            {/* Dish Type Filter */}
                            <FilterPopover 
                                title={translate('explore.dishType', lang)}
                                options={dishTypeOptions}
                                selectedValues={selectedDishTypes}
                                onChange={handleDishTypeChange}
                                icon={ChefHat}
                                lang={lang}
                                clearLabel={translate('explore.clearAll', lang)}
                            />
                            
                            {/* Continent Filter */}
                            <FilterPopover 
                                title={translate('explore.continent', lang)}
                                options={continentOptions}
                                selectedValues={selectedContinents}
                                onChange={handleContinentChange}
                                icon={Globe}
                                lang={lang}
                                clearLabel={translate('explore.clearAll', lang)}
                            />
                            
                            {/* Active Filter Tags */}
                            {activeFiltersCount > 0 && (
                                <>
                                    <div className="h-4 w-px bg-[#E8E4DC] mx-1 hidden sm:block"></div>
                                    
                                    {searchText.trim() && (
                                        <Badge 
                                            variant="secondary" 
                                            className="bg-[#6A1F2E]/10 text-[#6A1F2E] text-[10px] px-2 py-0.5 gap-1"
                                        >
                                            "{searchText.trim()}"
                                            <button onClick={() => setSearchText('')} data-testid="clear-search-tag">
                                                <X className="h-2.5 w-2.5" />
                                            </button>
                                        </Badge>
                                    )}

                                    {selectedDishTypes.map(dt => (
                                        <Badge 
                                            key={dt}
                                            variant="secondary" 
                                            className="bg-[#6A1F2E]/10 text-[#6A1F2E] text-[10px] px-2 py-0.5 gap-1"
                                        >
                                            {dishTypeOptions.find(d => d.value === dt)?.label}
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
                                            {continentOptions.find(cont => cont.value === c)?.label}
                                            <button onClick={() => handleContinentChange(selectedContinents.filter(v => v !== c))}>
                                                <X className="h-2.5 w-2.5" />
                                            </button>
                                        </Badge>
                                    ))}
                                    
                                    <button 
                                        onClick={clearAllFilters}
                                        className="text-[10px] text-[#6A1F2E] hover:underline ml-1"
                                        data-testid="clear-all-filters"
                                    >
                                        {translate('explore.clearAll', lang)}
                                    </button>
                                </>
                            )}
                            
                            {/* Recipe Count */}
                            <span className="text-xs text-[#7C7C7C] ml-auto" data-testid="recipe-count">
                                {filteredRecipes.length} {translate('explore.recipes', lang)}
                            </span>
                        </div>
                    </div>
                </section>
            )}

            {/* Main Content */}
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="flex gap-6">
                    
                    {/* CENTER: Main Content */}
                    <main className="flex-1 min-w-0">
                        {loading ? (
                            <div className="text-center py-12">
                                <ChefHat className="h-8 w-8 mx-auto text-[#6A1F2E] animate-pulse mb-3" />
                                <p className="text-sm text-[#7C7C7C] font-light">{translate('explore.loadingRecipes', lang)}</p>
                            </div>
                        ) : country ? (
                            /* Country Recipes View */
                            <>
                                <div className="flex items-center gap-2 mb-4 text-xs text-[#5C5C5C]">
                                    <MapPin className="h-3 w-3 text-[#6A1F2E]" />
                                    <span>{countryRecipes.length} {translate('explore.recipesFrom', lang)} {translateName(pageTitle, 'countries')}</span>
                                </div>

                                {countryRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {countryRecipes.map((recipe) => (
                                            <TranslatedRecipeCard key={recipe.slug} recipe={recipe} />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]">
                                        <p className="text-sm text-[#7C7C7C] font-light">{translate('explore.noRecipesFound', lang)}</p>
                                    </div>
                                )}
                            </>
                        ) : continent ? (
                            /* Continent Countries View */
                            <>
                                <h2 className="text-lg font-light mb-4 text-[#2C2C2C]" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                    {translate('explore.countriesIn', lang)} {translateName(selectedContinent, 'continents')}
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
                                                    <p className="text-[10px] text-[#7C7C7C]">{c.recipe_count} {translate('explore.recipes', lang)}</p>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]">
                                        <p className="text-sm text-[#7C7C7C] font-light">{translate('explore.noCountriesFound', lang)}</p>
                                    </div>
                                )}

                                {/* Other Continents */}
                                <div className="pt-6 border-t border-[#E8E4DC]">
                                    <h3 className="text-xs font-medium text-[#5C5C5C] mb-2 uppercase tracking-wide">
                                        {translate('explore.otherContinents', lang)}
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {continents.filter(c => c.slug !== continent).map((c) => (
                                            <Button
                                                key={c.slug}
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="border-[#E8E4DC] text-[#2C2C2C] hover:border-[#6A1F2E] hover:text-[#6A1F2E] text-xs h-7 px-3"
                                            >
                                                {translateName(c.name, 'continents')}
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            /* Main Explore View - Filtered Recipe Grid */
                            <>
                                {visibleRecipes.length > 0 ? (
                                    <>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="recipe-grid">
                                            {visibleRecipes.map((recipe) => (
                                                <RecipeCard key={recipe.slug} recipe={recipe} variant="editorial" deferFavoriteCheck />
                                            ))}
                                        </div>
                                        {hasMore && (
                                            <div className="text-center mt-6">
                                                <button
                                                    onClick={() => setVisibleCount(prev => prev + RECIPES_PER_PAGE)}
                                                    className="px-6 py-2 text-xs uppercase tracking-wider border border-[#6A1F2E] text-[#6A1F2E] hover:bg-[#6A1F2E] hover:text-white transition-colors"
                                                    data-testid="load-more-btn"
                                                >
                                                    {translate('explore.loadMore', lang)} ({filteredRecipes.length - visibleCount} {translate('explore.remaining', lang)})
                                                </button>
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="text-center py-12 bg-white border border-[#E8E4DC]" data-testid="no-results">
                                        <p className="text-sm text-[#7C7C7C] font-light">{translate('explore.noRecipesFound', lang)}</p>
                                        {activeFiltersCount > 0 && (
                                            <button 
                                                onClick={clearAllFilters}
                                                className="mt-3 text-xs text-[#6A1F2E] hover:underline"
                                            >
                                                {translate('explore.clearAll', lang)}
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Continent Quick Links */}
                                <div className="mt-10 pt-6 border-t border-[#E8E4DC]">
                                    <h3 className="text-base font-light text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                                        {translate('explore.byContinent', lang)}
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
                        <RankingSidebar recipes={topRecipes} getLocalizedPath={getLocalizedPath} lang={lang} />
                    </aside>
                </div>

                {/* Mobile Rankings (below content) */}
                <div className="lg:hidden mt-8">
                    <div className="bg-white border border-[#E8E4DC] p-4">
                        <h3 className="text-sm font-medium text-[#2C2C2C] mb-3" style={{ fontFamily: 'Cormorant Garamond, serif' }}>
                            {translate('explore.highestRated', lang)}
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
