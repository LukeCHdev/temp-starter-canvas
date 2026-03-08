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
    <nav className="flex items-center gap-2 text-xs text-muted-foreground mb-3" aria-label="Breadcrumb">
        <Link to={getLocalizedPath('/')} className="hover:text-primary flex items-center gap-1">
            <Home className="h-3 w-3" />
            {translate('common.home', lang)}
        </Link>
        <ChevronRight className="h-3 w-3" />
        <Link to={getLocalizedPath('/explore')} className={`hover:text-primary ${!continent ? 'text-primary font-medium' : ''}`}>
            {translate('nav.explore', lang)}
        </Link>
        {continent && (
            <>
                <ChevronRight className="h-3 w-3" />
                <Link 
                    to={getLocalizedPath(`/explore/${continent}`)} 
                    className={`hover:text-primary ${!country ? 'text-primary font-medium' : ''}`}
                >
                    {translateName(selectedContinent || continent.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()), 'continents')}
                </Link>
            </>
        )}
        {country && (
            <>
                <ChevronRight className="h-3 w-3" />
                <span className="text-primary font-medium">
                    {translateName(pageTitle, 'countries')}
                </span>
            </>
        )}
    </nav>
);

// Ranking Sidebar Component with translations
const RankingSidebar = ({ recipes, getLocalizedPath, lang }) => (
    <div className="bg-card border border-border p-4 sticky top-20">
        <h3 className="text-sm font-medium text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
            {translate('explore.highestRated', lang)}
        </h3>
        <div className="space-y-2">
            {recipes.slice(0, 8).map((recipe, index) => (
                <Link 
                    key={recipe.slug}
                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                    className="flex items-start gap-2 group py-1"
                >
                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-medium">
                        {index + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                        <p className="text-xs text-foreground group-hover:text-primary transition-colors line-clamp-2 leading-tight">
                            {recipe.recipe_name || recipe.title_original}
                        </p>
                        <div className="flex items-center gap-1 mt-0.5">
                            <Star className="h-2.5 w-2.5 fill-accent text-accent" />
                            <span className="text-[10px] text-muted-foreground">
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
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-border bg-card hover:border-primary transition-colors"
                    data-testid={`filter-${title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                    {Icon && <Icon className="h-3 w-3 text-primary" />}
                    <span className="text-foreground">{title}</span>
                    {selectedCount > 0 && (
                        <Badge className="bg-primary text-primary-foreground text-[10px] px-1.5 py-0 h-4 min-w-4">
                            {selectedCount}
                        </Badge>
                    )}
                    <ChevronDown className="h-3 w-3 text-muted-foreground" />
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-0" align="start">
                <ScrollArea className="h-64">
                    <div className="p-3 space-y-2">
                        {options.map((option) => (
                            <label 
                                key={option.value}
                                className="flex items-center gap-2 cursor-pointer hover:bg-muted p-1.5 rounded transition-colors"
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
                                    className="h-4 w-4 border-border data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                                />
                                <span className="text-xs text-foreground">{option.label}</span>
                            </label>
                        ))}
                    </div>
                </ScrollArea>
                {selectedCount > 0 && (
                    <div className="border-t border-border p-2">
                        <button 
                            onClick={() => onChange([])}
                            className="text-xs text-primary hover:underline w-full text-left"
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

    // Get translated continents
    const continentOptions = useMemo(() => 
        CONTINENT_KEYS.map(c => ({
            value: c.value,
            label: translate(`continents.${c.key}`, lang)
        })), [lang]
    );
    
    // Sync URL params with filter state
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

    // Load explore data
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

    // CLIENT-SIDE COMBINED FILTERING
    const filteredRecipes = useMemo(() => {
        let result = allRecipes;

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

        if (selectedDishTypes.length > 0) {
            result = result.filter(r => selectedDishTypes.includes(r.dish_type));
        }

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

    const handleContinentChange = (values) => {
        setSelectedContinents(values);
    };

    const handleContinentSelect = useCallback((continentSlug) => {
        navigate(getLocalizedPath(`/explore/${continentSlug}`));
    }, [navigate, getLocalizedPath]);

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

    const activeFiltersCount = selectedDishTypes.length + selectedContinents.length + (searchText.trim() ? 1 : 0);

    const RECIPES_PER_PAGE = 24;
    const [visibleCount, setVisibleCount] = useState(RECIPES_PER_PAGE);

    useEffect(() => {
        setVisibleCount(RECIPES_PER_PAGE);
    }, [searchText, selectedDishTypes, selectedContinents]);

    const visibleRecipes = useMemo(() => 
        filteredRecipes.slice(0, visibleCount), 
        [filteredRecipes, visibleCount]
    );
    const hasMore = visibleCount < filteredRecipes.length;

    const breadcrumbProps = useMemo(() => ({
        continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, lang
    }), [continent, country, selectedContinent, pageTitle, getLocalizedPath, translateName, lang]);

    const seoPath = useMemo(() => {
        if (country) return `/explore/${continent}/${country}`;
        if (continent) return `/explore/${continent}`;
        return '/explore';
    }, [continent, country]);

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
        <div className="min-h-screen bg-background" data-testid="explore-page">
            <ExploreSEO 
                continent={selectedContinent}
                country={pageTitle}
                path={seoPath}
                breadcrumbs={seoBreadcrumbs}
            />
            
            {/* Header */}
            <section className="bg-card border-b border-border py-6 px-4">
                <div className="max-w-6xl mx-auto">
                    <Breadcrumb {...breadcrumbProps} />
                    <h1 className="text-2xl sm:text-3xl font-light text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                        {country ? translateName(pageTitle, 'countries') : 
                         continent ? translateName(pageTitle, 'continents') : 
                         translate('explore.title', lang)}
                    </h1>
                </div>
            </section>

            {/* TOP FILTER BAR */}
            {!continent && !country && (
                <section className="bg-muted border-b border-border py-3 px-4 sticky top-16 z-40">
                    <div className="max-w-6xl mx-auto">
                        <div className="flex items-center gap-3 flex-wrap">
                            {/* Search Input */}
                            <div className="relative flex-shrink-0 w-full sm:w-auto sm:min-w-[220px]">
                                <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                                <input
                                    type="text"
                                    value={searchText}
                                    onChange={(e) => setSearchText(e.target.value)}
                                    placeholder={translate('homepage.hero.searchHelper', lang)}
                                    className="w-full pl-8 pr-3 py-1.5 text-xs border border-border bg-card focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors"
                                    data-testid="explore-search-input"
                                />
                            </div>

                            <span className="text-xs text-muted-foreground uppercase tracking-wide hidden sm:inline">
                                {translate('explore.filters', lang)}:
                            </span>
                            
                            <FilterPopover 
                                title={translate('explore.dishType', lang)}
                                options={dishTypeOptions}
                                selectedValues={selectedDishTypes}
                                onChange={handleDishTypeChange}
                                icon={ChefHat}
                                lang={lang}
                                clearLabel={translate('explore.clearAll', lang)}
                            />
                            
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
                                    <div className="h-4 w-px bg-border mx-1 hidden sm:block"></div>
                                    
                                    {searchText.trim() && (
                                        <Badge 
                                            variant="secondary" 
                                            className="bg-primary/10 text-primary text-[10px] px-2 py-0.5 gap-1"
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
                                            className="bg-primary/10 text-primary text-[10px] px-2 py-0.5 gap-1"
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
                                            className="bg-primary/10 text-primary text-[10px] px-2 py-0.5 gap-1"
                                        >
                                            {continentOptions.find(cont => cont.value === c)?.label}
                                            <button onClick={() => handleContinentChange(selectedContinents.filter(v => v !== c))}>
                                                <X className="h-2.5 w-2.5" />
                                            </button>
                                        </Badge>
                                    ))}
                                    
                                    <button 
                                        onClick={clearAllFilters}
                                        className="text-[10px] text-primary hover:underline ml-1"
                                        data-testid="clear-all-filters"
                                    >
                                        {translate('explore.clearAll', lang)}
                                    </button>
                                </>
                            )}
                            
                            <span className="text-xs text-muted-foreground ml-auto" data-testid="recipe-count">
                                {filteredRecipes.length} {translate('explore.recipes', lang)}
                            </span>
                        </div>
                    </div>
                </section>
            )}

            {/* Main Content */}
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="flex gap-6">
                    
                    <main className="flex-1 min-w-0">
                        {loading ? (
                            <div className="text-center py-12">
                                <ChefHat className="h-8 w-8 mx-auto text-primary animate-pulse mb-3" />
                                <p className="text-sm text-muted-foreground font-light">{translate('explore.loadingRecipes', lang)}</p>
                            </div>
                        ) : country ? (
                            <>
                                <div className="flex items-center gap-2 mb-4 text-xs text-muted-foreground">
                                    <MapPin className="h-3 w-3 text-primary" />
                                    <span>{countryRecipes.length} {translate('explore.recipesFrom', lang)} {translateName(pageTitle, 'countries')}</span>
                                </div>

                                {countryRecipes.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {countryRecipes.map((recipe) => (
                                            <TranslatedRecipeCard key={recipe.slug} recipe={recipe} />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-card border border-border">
                                        <p className="text-sm text-muted-foreground font-light">{translate('explore.noRecipesFound', lang)}</p>
                                    </div>
                                )}
                            </>
                        ) : continent ? (
                            <>
                                <h2 className="text-lg font-light mb-4 text-foreground" style={{ fontFamily: 'var(--font-heading)' }}>
                                    {translate('explore.countriesIn', lang)} {translateName(selectedContinent, 'continents')}
                                </h2>

                                {countries.length > 0 ? (
                                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
                                        {countries.map((c) => (
                                            <Link
                                                key={c.slug}
                                                to={getLocalizedPath(`/explore/${continent}/${c.slug}`)}
                                                className="bg-card border border-border p-3 hover:border-primary transition-colors flex items-center gap-2"
                                            >
                                                <Globe className="h-4 w-4 text-primary" />
                                                <div>
                                                    <h3 className="font-medium text-foreground text-sm">{translateName(c.name, 'countries')}</h3>
                                                    <p className="text-[10px] text-muted-foreground">{c.recipe_count} {translate('explore.recipes', lang)}</p>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 bg-card border border-border">
                                        <p className="text-sm text-muted-foreground font-light">{translate('explore.noCountriesFound', lang)}</p>
                                    </div>
                                )}

                                {/* Other Continents */}
                                <div className="pt-6 border-t border-border">
                                    <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
                                        {translate('explore.otherContinents', lang)}
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {continents.filter(c => c.slug !== continent).map((c) => (
                                            <Button
                                                key={c.slug}
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="border-border text-foreground hover:border-primary hover:text-primary text-xs h-7 px-3"
                                            >
                                                {translateName(c.name, 'continents')}
                                            </Button>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
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
                                                    className="px-6 py-2 text-xs uppercase tracking-wider border border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
                                                    data-testid="load-more-btn"
                                                >
                                                    {translate('explore.loadMore', lang)} ({filteredRecipes.length - visibleCount} {translate('explore.remaining', lang)})
                                                </button>
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="text-center py-12 bg-card border border-border" data-testid="no-results">
                                        <p className="text-sm text-muted-foreground font-light">{translate('explore.noRecipesFound', lang)}</p>
                                        {activeFiltersCount > 0 && (
                                            <button 
                                                onClick={clearAllFilters}
                                                className="mt-3 text-xs text-primary hover:underline"
                                            >
                                                {translate('explore.clearAll', lang)}
                                            </button>
                                        )}
                                    </div>
                                )}

                                {/* Continent Quick Links */}
                                <div className="mt-10 pt-6 border-t border-border">
                                    <h3 className="text-base font-light text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                                        {translate('explore.byContinent', lang)}
                                    </h3>
                                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                                        {continents.map((c) => (
                                            <button
                                                key={c.slug}
                                                onClick={() => handleContinentSelect(c.slug)}
                                                className="bg-card border border-border p-3 hover:border-primary transition-colors text-center group"
                                            >
                                                <h4 className="font-medium text-foreground group-hover:text-primary transition-colors text-xs">
                                                    {translateName(c.name, 'continents')}
                                                </h4>
                                                <p className="text-[10px] text-muted-foreground mt-0.5">
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

                {/* Mobile Rankings */}
                <div className="lg:hidden mt-8">
                    <div className="bg-card border border-border p-4">
                        <h3 className="text-sm font-medium text-foreground mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
                            {translate('explore.highestRated', lang)}
                        </h3>
                        <div className="grid grid-cols-2 gap-2">
                            {topRecipes.slice(0, 6).map((recipe, index) => (
                                <Link 
                                    key={recipe.slug}
                                    to={getLocalizedPath(`/recipe/${recipe.slug}`)}
                                    className="flex items-start gap-2 p-2 bg-background hover:bg-muted transition-colors"
                                >
                                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-medium">
                                        {index + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs text-foreground line-clamp-2">
                                            {recipe.recipe_name || recipe.title_original}
                                        </p>
                                        <div className="flex items-center gap-1 mt-0.5">
                                            <Star className="h-2.5 w-2.5 fill-accent text-accent" />
                                            <span className="text-[10px] text-muted-foreground">
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
