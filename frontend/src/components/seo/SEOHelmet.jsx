import { Helmet } from 'react-helmet';

/**
 * SEO component for recipe pages with JSON-LD structured data
 */
export const RecipeSEO = ({ recipe, url }) => {
    if (!recipe) return null;
    
    const recipeName = recipe.recipe_name || recipe.title_original || 'Recipe';
    const description = recipe.history_summary || recipe.characteristic_profile || `Authentic ${recipeName} recipe`;
    const country = recipe.origin_country || recipe.country || 'Global';
    const region = recipe.origin_region || recipe.region || '';
    const imageUrl = recipe.photos?.[0]?.image_url || '';
    
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
    
    // Calculate aggregate rating
    const hasRating = recipe.average_rating && recipe.ratings_count;
    
    // JSON-LD Recipe structured data
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipeName,
        "description": description,
        "author": {
            "@type": "Organization",
            "name": "Sous-Chef Linguine AI"
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
                "ratingCount": recipe.ratings_count
            }
        }),
        "countryOfOrigin": {
            "@type": "Country",
            "name": country
        }
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
                "item": url?.replace(`/recipe/${recipe.slug}`, '') || '/'
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": "Explore",
                "item": `${url?.replace(`/recipe/${recipe.slug}`, '')}/explore`
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": country,
                "item": `${url?.replace(`/recipe/${recipe.slug}`, '')}/explore/${recipe.continent?.toLowerCase().replace(' ', '-')}/${country.toLowerCase().replace(' ', '-')}`
            },
            {
                "@type": "ListItem",
                "position": 4,
                "name": recipeName
            }
        ]
    };
    
    return (
        <Helmet>
            {/* Basic Meta Tags */}
            <title>{`${recipeName} - Authentic ${country} Recipe | Sous Chef Linguine`}</title>
            <meta name="description" content={`${description.substring(0, 155)}...`} />
            <link rel="canonical" href={url} />
            
            {/* Open Graph Tags */}
            <meta property="og:title" content={`${recipeName} - Authentic ${country} Recipe`} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content="article" />
            <meta property="og:url" content={url} />
            {imageUrl && <meta property="og:image" content={imageUrl} />}
            <meta property="og:site_name" content="Sous Chef Linguine" />
            
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
export const PageSEO = ({ title, description, url, type = 'website' }) => {
    return (
        <Helmet>
            <title>{`${title} | Sous Chef Linguine`}</title>
            <meta name="description" content={description} />
            <link rel="canonical" href={url} />
            
            <meta property="og:title" content={title} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content={type} />
            <meta property="og:url" content={url} />
            <meta property="og:site_name" content="Sous Chef Linguine" />
            
            <meta name="twitter:card" content="summary" />
            <meta name="twitter:title" content={title} />
            <meta name="twitter:description" content={description} />
        </Helmet>
    );
};

/**
 * SEO component for explore/category pages with breadcrumbs
 */
export const ExploreSEO = ({ title, description, url, breadcrumbs = [] }) => {
    const breadcrumbJsonLd = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs.map((item, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.name,
            "item": item.url
        }))
    };
    
    return (
        <Helmet>
            <title>{`${title} | Sous Chef Linguine`}</title>
            <meta name="description" content={description} />
            <link rel="canonical" href={url} />
            
            <meta property="og:title" content={title} />
            <meta property="og:description" content={description} />
            <meta property="og:type" content="website" />
            <meta property="og:url" content={url} />
            <meta property="og:site_name" content="Sous Chef Linguine" />
            
            <meta name="twitter:card" content="summary" />
            <meta name="twitter:title" content={title} />
            <meta name="twitter:description" content={description} />
            
            <script type="application/ld+json">
                {JSON.stringify(breadcrumbJsonLd)}
            </script>
        </Helmet>
    );
};
