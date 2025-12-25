"""
Prerender Routes - API endpoints for prerender verification and testing

These routes help verify that prerendering is working correctly.
"""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from services.prerender_service import prerender_service, CRAWLER_USER_AGENTS, _db
import logging
import json
import re

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prerender"])


async def get_recipe_from_db(slug: str, language: str = 'en'):
    """Fetch recipe data from database for SEO fallback"""
    if _db is None:
        return None
    
    try:
        recipe = await _db.recipes.find_one(
            {"slug": slug, "published": True},
            {"_id": 0}
        )
        
        if not recipe:
            return None
        
        # Get translation if available
        translations = recipe.get('translations', {})
        translation = translations.get(language, {})
        has_translation = translation.get('status') == 'ready'
        
        # Use translated content if available, otherwise English
        if has_translation:
            name = translation.get('recipe_name') or recipe.get('recipe_name', 'Recipe')
            description = translation.get('history_summary') or translation.get('characteristic_profile') or ''
            ingredients = translation.get('ingredients', recipe.get('ingredients', []))
            instructions = translation.get('instructions', recipe.get('instructions', []))
        else:
            name = recipe.get('recipe_name', 'Recipe')
            description = recipe.get('history_summary') or recipe.get('characteristic_profile') or recipe.get('origin_story', '')
            ingredients = recipe.get('ingredients', [])
            instructions = recipe.get('instructions', [])
        
        return {
            'name': name,
            'description': description,
            'country': recipe.get('origin_country', 'Unknown'),
            'region': recipe.get('origin_region', ''),
            'ingredients': ingredients,
            'instructions': instructions,
            'photo_url': recipe.get('photos', [{}])[0].get('image_url', '') if recipe.get('photos') else '',
            'slug': slug,
            'language': language
        }
    except Exception as e:
        logger.error(f"Error fetching recipe {slug}: {e}")
        return None


def generate_recipe_html(recipe_data: dict, language: str, site_url: str) -> str:
    """Generate full SEO-optimized HTML for a recipe page"""
    
    name = recipe_data['name']
    description = recipe_data['description'][:300] if recipe_data['description'] else f"Authentic {name} recipe"
    country = recipe_data['country']
    region = recipe_data['region']
    slug = recipe_data['slug']
    ingredients = recipe_data['ingredients']
    instructions = recipe_data['instructions']
    photo_url = recipe_data['photo_url']
    
    # Build ingredients HTML
    ingredients_html = ""
    ingredients_json = []
    if ingredients:
        ingredients_html = "<ul>"
        for ing in ingredients:
            item = ing.get('item', '') if isinstance(ing, dict) else str(ing)
            amount = ing.get('amount', '') if isinstance(ing, dict) else ''
            unit = ing.get('unit', '') if isinstance(ing, dict) else ''
            full_ing = f"{amount} {unit} {item}".strip()
            ingredients_html += f"<li>{full_ing}</li>"
            ingredients_json.append(full_ing)
        ingredients_html += "</ul>"
    
    # Build instructions HTML
    instructions_html = ""
    instructions_json = []
    if instructions:
        instructions_html = "<ol>"
        for i, step in enumerate(instructions):
            text = step.get('instruction', '') if isinstance(step, dict) else str(step)
            instructions_html += f"<li>{text}</li>"
            instructions_json.append({
                "@type": "HowToStep",
                "position": i + 1,
                "text": text
            })
        instructions_html += "</ol>"
    
    # JSON-LD for Recipe
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": name,
        "description": description,
        "author": {"@type": "Organization", "name": "Sous Chef Linguine"},
        "publisher": {"@type": "Organization", "name": "Sous Chef Linguine", "url": site_url},
        "recipeIngredient": ingredients_json,
        "recipeInstructions": instructions_json,
        "recipeCuisine": country,
        "countryOfOrigin": {"@type": "Country", "name": country},
        "inLanguage": language
    }
    
    if photo_url:
        json_ld["image"] = photo_url
    
    # Breadcrumb JSON-LD
    breadcrumb_json_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{site_url}/{language}/"},
            {"@type": "ListItem", "position": 2, "name": "Explore", "item": f"{site_url}/{language}/explore"},
            {"@type": "ListItem", "position": 3, "name": country, "item": f"{site_url}/{language}/explore/{country.lower().replace(' ', '-')}"},
            {"@type": "ListItem", "position": 4, "name": name}
        ]
    }
    
    # Localized section headers
    section_headers = {
        'en': {'history': 'History & Origin', 'ingredients': 'Ingredients', 'instructions': 'Instructions'},
        'es': {'history': 'Historia y Origen', 'ingredients': 'Ingredientes', 'instructions': 'Instrucciones'},
        'it': {'history': 'Storia e Origine', 'ingredients': 'Ingredienti', 'instructions': 'Istruzioni'},
        'fr': {'history': 'Histoire et Origine', 'ingredients': 'Ingrédients', 'instructions': 'Instructions'},
        'de': {'history': 'Geschichte und Herkunft', 'ingredients': 'Zutaten', 'instructions': 'Anweisungen'}
    }
    headers = section_headers.get(language, section_headers['en'])
    
    return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Authentic {country} Recipe | Sous Chef Linguine</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{site_url}/{language}/recipe/{slug}">
    
    <!-- Hreflang tags -->
    <link rel="alternate" hreflang="en" href="{site_url}/en/recipe/{slug}">
    <link rel="alternate" hreflang="es" href="{site_url}/es/recipe/{slug}">
    <link rel="alternate" hreflang="it" href="{site_url}/it/recipe/{slug}">
    <link rel="alternate" hreflang="fr" href="{site_url}/fr/recipe/{slug}">
    <link rel="alternate" hreflang="de" href="{site_url}/de/recipe/{slug}">
    <link rel="alternate" hreflang="x-default" href="{site_url}/en/recipe/{slug}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{name} - Authentic {country} Recipe">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{site_url}/{language}/recipe/{slug}">
    {f'<meta property="og:image" content="{photo_url}">' if photo_url else ''}
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {json.dumps(json_ld)}
    </script>
    <script type="application/ld+json">
    {json.dumps(breadcrumb_json_ld)}
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="/{language}/">Sous Chef Linguine</a>
            <a href="/{language}/explore">Explore</a>
            <a href="/{language}/techniques">Techniques</a>
            <a href="/{language}/about">About</a>
        </nav>
    </header>
    
    <main>
        <article itemscope itemtype="https://schema.org/Recipe">
            <h1 itemprop="name">{name}</h1>
            <p>📍 {country}{f' • {region}' if region else ''}</p>
            
            {f'<img src="{photo_url}" alt="{name}" itemprop="image">' if photo_url else ''}
            
            <section>
                <h2>{headers['history']}</h2>
                <p itemprop="description">{description}</p>
            </section>
            
            <section>
                <h2>🧺 {headers['ingredients']}</h2>
                {ingredients_html}
            </section>
            
            <section>
                <h2>👨‍🍳 {headers['instructions']}</h2>
                {instructions_html}
            </section>
        </article>
    </main>
    
    <footer>
        <nav>
            <a href="/{language}/explore">More Recipes</a>
            <a href="/{language}/privacy">Privacy Policy</a>
            <a href="/{language}/terms">Terms of Service</a>
            <a href="/{language}/contact">Contact</a>
        </nav>
        <p>© 2025 Sous Chef Linguine. All rights reserved.</p>
    </footer>
    
    <div id="root"></div>
    <noscript>JavaScript is required for full functionality.</noscript>
</body>
</html>"""


@router.get("/prerender/test/{path:path}")
async def test_prerender(
    path: str,
    request: Request,
    simulate_bot: bool = Query(default=True, description="Simulate a crawler request")
):
    """
    Test endpoint to verify prerendering for a specific path.
    
    Use ?simulate_bot=true to see what Googlebot would receive.
    Use ?simulate_bot=false to see what regular users receive.
    """
    full_path = f"/{path}"
    
    if simulate_bot:
        # Simulate Googlebot
        user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    else:
        user_agent = request.headers.get('user-agent', 'Regular User')
    
    should_prerender = prerender_service.should_prerender(full_path, user_agent)
    is_crawler = prerender_service.is_crawler(user_agent)
    
    result = {
        "path": full_path,
        "user_agent": user_agent[:100],
        "is_crawler": is_crawler,
        "should_prerender": should_prerender,
        "prerender_enabled": prerender_service.enabled,
        "prerender_url": prerender_service.prerender_url,
        "site_url": prerender_service.site_url
    }
    
    if simulate_bot and should_prerender:
        # Try to get prerendered content
        html_content, status_code = await prerender_service.get_prerendered_content(full_path)
        
        if html_content:
            result["prerender_status"] = "success"
            result["content_length"] = len(html_content)
            result["has_h1"] = "<h1" in html_content.lower()
            result["has_json_ld"] = "application/ld+json" in html_content.lower()
            result["has_canonical"] = 'rel="canonical"' in html_content.lower()
            result["has_hreflang"] = "hreflang" in html_content.lower()
        else:
            # Use fallback
            fallback_html = prerender_service.generate_static_html(full_path)
            result["prerender_status"] = "fallback"
            result["fallback_content_length"] = len(fallback_html)
            result["fallback_has_h1"] = "<h1" in fallback_html.lower()
            result["fallback_has_json_ld"] = "application/ld+json" in fallback_html.lower()
    
    return JSONResponse(content=result)


@router.get("/prerender/verify/{path:path}")
async def verify_prerender(path: str):
    """
    Verify that a path would be prerendered correctly.
    Returns the actual HTML that would be served to crawlers.
    """
    full_path = f"/{path}"
    
    # Get prerendered content
    html_content, status_code = await prerender_service.get_prerendered_content(full_path)
    
    if html_content:
        return HTMLResponse(
            content=html_content,
            headers={"X-Prerendered": "true"}
        )
    else:
        # Return fallback HTML
        fallback_html = prerender_service.generate_static_html(full_path)
        return HTMLResponse(
            content=fallback_html,
            headers={"X-Prerendered": "fallback"}
        )


@router.get("/prerender/fallback/{path:path}")
async def get_fallback_html(path: str):
    """
    Get the fallback static HTML for a specific path.
    This is what crawlers would receive if the prerender service is unavailable.
    """
    full_path = f"/{path}"
    fallback_html = prerender_service.generate_static_html(full_path)
    
    return HTMLResponse(
        content=fallback_html,
        headers={
            "X-Prerendered": "fallback",
            "X-Path": full_path
        }
    )


@router.get("/prerender/status")
async def prerender_status():
    """
    Get the current status of the prerender service.
    """
    return {
        "enabled": prerender_service.enabled,
        "prerender_url": prerender_service.prerender_url,
        "site_url": prerender_service.site_url,
        "has_token": bool(prerender_service.prerender_token),
        "crawler_count": len(CRAWLER_USER_AGENTS),
        "sample_crawlers": CRAWLER_USER_AGENTS[:5]
    }


@router.get("/prerender/crawlers")
async def list_crawlers():
    """
    List all known crawler user agents that trigger prerendering.
    """
    return {
        "crawlers": CRAWLER_USER_AGENTS,
        "count": len(CRAWLER_USER_AGENTS)
    }


@router.get("/prerender/recipe/{lang}/{slug}")
async def get_recipe_prerender(lang: str, slug: str):
    """
    Get prerendered HTML for a specific recipe with full content from database.
    This is the SEO-optimized fallback for recipe pages.
    """
    recipe_data = await get_recipe_from_db(slug, lang)
    
    if recipe_data:
        html = generate_recipe_html(recipe_data, lang, prerender_service.site_url)
        return HTMLResponse(
            content=html,
            headers={
                "X-Prerendered": "database",
                "X-Recipe": slug,
                "X-Language": lang
            }
        )
    else:
        # Fallback to basic HTML
        fallback_html = prerender_service.generate_static_html(f"/{lang}/recipe/{slug}")
        return HTMLResponse(
            content=fallback_html,
            headers={
                "X-Prerendered": "fallback",
                "X-Recipe": slug
            }
        )
