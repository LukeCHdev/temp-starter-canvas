import { Helmet } from 'react-helmet';
import { useLanguage } from '@/context/LanguageContext';

// Base domain for all canonical URLs
const BASE_DOMAIN = 'https://www.souscheflinguine.com';

/**
 * SEO component for recipe pages with JSON-LD structured data
 */
export const RecipeSEO = ({ recipe, slug }) => {
    const { language } = useLanguage();
    
    if (!recipe) return null;
    
    const recipeName = recipe.recipe_name || recipe.title_original || 'Recipe';
    const description = recipe.history_summary || recipe.characteristic_profile || `Authentic ${recipeName} recipe`;
    const country = recipe.origin_country || recipe.country || 'Global';
    const region = recipe.origin_region || recipe.region || '';
    const imageUrl = recipe.photos?.[0]?.image_url || '';
    
    // Canonical URL with language prefix
    const canonicalUrl = `${BASE_DOMAIN}/${language}/recipe/${slug}`;
    
    // Build ingredients array for JSON-LD
    const ingredients = recipe.ingredients?.map(ing => 
        `${ing.amount} ${ing.unit} ${ing.item}${ing.notes ? ` (${ing.notes})` : ''}`
    ) || [];
    
    // Build instructions array for JSON-LD
    const instructions = recipe.instructions?.map((step, index) => ({
        "@type": "HowToStep",
        "position": index + 1,
        "text": typeof step === 'string' ? step : step.instruction
    })) || [];
    
    // Calculate aggregate rating - only include if we have real data
    const hasRating = recipe.average_rating && recipe.ratings_count && recipe.ratings_count > 0;
    
    // JSON-LD Recipe structured data
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipeName,
        "description": description,
        "author": {
            "@type": "Organization",
            "name": "Sous Chef Linguine"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Sous Chef Linguine",
            "url": BASE_DOMAIN
        },
        "datePublished": recipe.date_fetched || new Date().toISOString(),
        "image": imageUrl || undefined,
        "recipeIngredient": ingredients,
        "recipeInstructions": instructions,
        "recipeCuisine": country,
        "recipeCategory": "Main Course",
        ...(hasRating && {
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": recipe.average_rating,
                "ratingCount": recipe.ratings_count,
                "bestRating": 5,
                "worstRating": 1
            }
        }),
        "countryOfOrigin": {
            "@type": "Country",
            "name": country
        },
        "inLanguage": language
    };
    
    // Breadcrumb JSON-LD
    const breadcrumbJsonLd = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": `${BASE_DOMAIN}/${language}/`
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Explore",
                "item": `${BASE_DOMAIN}/${language}/explore`
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": country,
                "item": `${BASE_DOMAIN}/${language}/explore/${recipe.continent?.toLowerCase().replace(' ', '-')}/${country.toLowerCase().replace(' ', '-')}`
            },
            {
                "@type": "ListItem",
                "position": 4,
                "name": recipeName
            }
        ]
    };
    
    // Generate hreflang links for all supported languages
    const languages = ['en', 'it', 'fr', 'es', 'de'];
    
    return (
        <Helmet>
            {/* Basic Meta Tags */}
            <title>{`${recipeName} - Authentic ${country} Recipe | Sous Chef Linguine`}</title>
            <meta name="description" content={`${description.substring(0, 155)}...`} />
            <link rel="canonical" href={canonicalUrl} />
            
            {/* Hreflang Tags */}
            {languages.map(lang => (
                <link 
                    key={lang}
                    rel="alternate" 
                    hreflang={lang} 
                    href={`${BASE_DOMAIN}/${lang}/recipe/${slug}`} 
                />
            ))}
            <link rel="alternate" hreflang="x-default" href={`${BASE_DOMAIN}/en/recipe/${slug}`} />
            
            {/* Open Graph Tags */}
            <meta property="og:title" content={`${recipeName} - Authentic ${country} Recipe`} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content="article" />
            <meta property="og:url" content={canonicalUrl} />
            {imageUrl && <meta property="og:image" content={imageUrl} />}
            <meta property="og:site_name" content="Sous Chef Linguine" />
            <meta property="og:locale" content={language === 'en' ? 'en_US' : language === 'it' ? 'it_IT' : language === 'fr' ? 'fr_FR' : language === 'es' ? 'es_ES' : 'de_DE'} />
            
            {/* Twitter Card Tags */}
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content={`${recipeName} - Authentic ${country} Recipe`} />
            <meta name="twitter:description" content={description} />
            {imageUrl && <meta name="twitter:image" content={imageUrl} />}
            
            {/* JSON-LD Structured Data */}
            <script type="application/ld+json">
                {JSON.stringify(jsonLd)}
            </script>
            <script type="application/ld+json">
                {JSON.stringify(breadcrumbJsonLd)}
            </script>
        </Helmet>
    );
};

/**
 * SEO component for general pages
 */
export const PageSEO = ({ 
    title, 
    description, 
    path = '', 
    type = 'website',
    noIndex = false 
}) => {
    const { language } = useLanguage();
    const canonicalUrl = `${BASE_DOMAIN}/${language}${path}`;
    const languages = ['en', 'it', 'fr', 'es', 'de'];
    
    return (
        <Helmet>
            <html lang={language} />
            <title>{`${title} | Sous Chef Linguine`}</title>
            <meta name="description" content={description} />
            <link rel="canonical" href={canonicalUrl} />
            {noIndex && <meta name="robots" content="noindex, nofollow" />}
            
            {/* Hreflang Tags */}
            {languages.map(lang => (
                <link 
                    key={lang}
                    rel="alternate" 
                    hreflang={lang} 
                    href={`${BASE_DOMAIN}/${lang}${path}`} 
                />
            ))}
            <link rel="alternate" hreflang="x-default" href={`${BASE_DOMAIN}/en${path}`} />
            
            <meta property="og:title" content={title} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content={type} />
            <meta property="og:url" content={canonicalUrl} />
            <meta property="og:site_name" content="Sous Chef Linguine" />
            <meta property="og:locale" content={language === 'en' ? 'en_US' : language === 'it' ? 'it_IT' : language === 'fr' ? 'fr_FR' : language === 'es' ? 'es_ES' : 'de_DE'} />
            
            <meta name="twitter:card" content="summary" />
            <meta name="twitter:title" content={title} />
            <meta name="twitter:description" content={description} />
        </Helmet>
    );
};

/**
 * SEO component for explore/category pages with breadcrumbs
 */
export const ExploreSEO = ({ title, description, path = '/explore', breadcrumbs = [] }) => {
    const { language } = useLanguage();
    const canonicalUrl = `${BASE_DOMAIN}/${language}${path}`;
    const languages = ['en', 'it', 'fr', 'es', 'de'];
    
    const breadcrumbJsonLd = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs.map((item, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.name,
            "item": `${BASE_DOMAIN}/${language}${item.path}`
        }))
    };
    
    return (
        <Helmet>
            <html lang={language} />
            <title>{`${title} | Sous Chef Linguine`}</title>
            <meta name="description" content={description} />
            <link rel="canonical" href={canonicalUrl} />
            
            {/* Hreflang Tags */}
            {languages.map(lang => (
                <link 
                    key={lang}
                    rel="alternate" 
                    hreflang={lang} 
                    href={`${BASE_DOMAIN}/${lang}${path}`} 
                />
            ))}
            <link rel="alternate" hreflang="x-default" href={`${BASE_DOMAIN}/en${path}`} />
            
            <meta property="og:title" content={title} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content="website" />
            <meta property="og:url" content={canonicalUrl} />
            <meta property="og:site_name" content="Sous Chef Linguine" />
            <meta property="og:locale" content={language === 'en' ? 'en_US' : language === 'it' ? 'it_IT' : language === 'fr' ? 'fr_FR' : language === 'es' ? 'es_ES' : 'de_DE'} />
            
            <meta name="twitter:card" content="summary" />
            <meta name="twitter:title" content={title} />
            <meta name="twitter:description" content={description} />
            
            <script type="application/ld+json">
                {JSON.stringify(breadcrumbJsonLd)}
            </script>
        </Helmet>
    );
};

/**
 * SEO component for the homepage
 */
export const HomeSEO = () => {
    const { language } = useLanguage();
    const languages = ['en', 'it', 'fr', 'es', 'de'];
    
    const titles = {
        en: 'Sous Chef Linguine | Authentic Global Recipe Archive',
        it: 'Sous Chef Linguine | Archivio di Ricette Autentiche Globali',
        fr: 'Sous Chef Linguine | Archives de Recettes Authentiques du Monde',
        es: 'Sous Chef Linguine | Archivo de Recetas Auténticas Globales',
        de: 'Sous Chef Linguine | Authentisches Globales Rezeptarchiv'
    };
    
    const descriptions = {
        en: 'An editorial and cultural archive dedicated to preserving and documenting authentic traditional recipes from around the world. No adaptation, no compromise - just authentic culinary heritage.',
        it: 'Un archivio editoriale e culturale dedicato alla conservazione e documentazione di ricette tradizionali autentiche da tutto il mondo. Nessun adattamento, nessun compromesso - solo autentico patrimonio culinario.',
        fr: 'Une archive éditoriale et culturelle dédiée à la préservation et à la documentation de recettes traditionnelles authentiques du monde entier. Pas d\'adaptation, pas de compromis - juste un patrimoine culinaire authentique.',
        es: 'Un archivo editorial y cultural dedicado a preservar y documentar recetas tradicionales auténticas de todo el mundo. Sin adaptación, sin compromiso - solo patrimonio culinario auténtico.',
        de: 'Ein redaktionelles und kulturelles Archiv, das der Bewahrung und Dokumentation authentischer traditioneller Rezepte aus aller Welt gewidmet ist. Keine Anpassung, kein Kompromiss - nur authentisches kulinarisches Erbe.'
    };
    
    return (
        <Helmet>
            <html lang={language} />
            <title>{titles[language]}</title>
            <meta name="description" content={descriptions[language]} />
            <link rel="canonical" href={`${BASE_DOMAIN}/${language}/`} />
            
            {/* Hreflang Tags */}
            {languages.map(lang => (
                <link 
                    key={lang}
                    rel="alternate" 
                    hreflang={lang} 
                    href={`${BASE_DOMAIN}/${lang}/`} 
                />
            ))}
            <link rel="alternate" hreflang="x-default" href={`${BASE_DOMAIN}/`} />
            
            <meta property="og:title" content={titles[language]} />
            <meta property="og:description" content={descriptions[language]} />
            <meta property="og:type" content="website" />
            <meta property="og:url" content={`${BASE_DOMAIN}/${language}/`} />
            <meta property="og:site_name" content="Sous Chef Linguine" />
            <meta property="og:locale" content={language === 'en' ? 'en_US' : language === 'it' ? 'it_IT' : language === 'fr' ? 'fr_FR' : language === 'es' ? 'es_ES' : 'de_DE'} />
            
            <meta name="twitter:card" content="summary_large_image" />
            <meta name="twitter:title" content={titles[language]} />
            <meta name="twitter:description" content={descriptions[language]} />
        </Helmet>
    );
};
