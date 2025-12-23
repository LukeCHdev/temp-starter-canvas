"""
Dynamic Multilingual Sitemap Generator
Generates XML sitemap with hreflang annotations for all supported languages.
Implements caching with periodic rebuild for performance.
"""

from fastapi import APIRouter, Response, Request
from fastapi.responses import Response as FastAPIResponse
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import json
import asyncio

router = APIRouter()

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'es', 'it', 'fr', 'de']
DEFAULT_LANGUAGE = 'en'

# Cache settings
SITEMAP_CACHE_FILE = '/tmp/sitemap_cache.xml'
SITEMAP_CACHE_META = '/tmp/sitemap_cache_meta.json'
CACHE_TTL_HOURS = 24  # Rebuild daily

# Base URL - should come from environment in production
BASE_URL = os.environ.get('SITE_URL', 'https://souscheflinguine.com')

# Database reference (set by main server)
_db = None

def set_sitemap_db(database):
    """Set the database reference for sitemap generation."""
    global _db
    _db = database


def get_cache_metadata() -> dict:
    """Read cache metadata to check if rebuild is needed."""
    try:
        if os.path.exists(SITEMAP_CACHE_META):
            with open(SITEMAP_CACHE_META, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_cache_metadata(metadata: dict):
    """Save cache metadata."""
    try:
        with open(SITEMAP_CACHE_META, 'w') as f:
            json.dump(metadata, f)
    except Exception:
        pass


def is_cache_valid() -> bool:
    """Check if cached sitemap is still valid."""
    metadata = get_cache_metadata()
    if not metadata.get('generated_at'):
        return False
    
    generated_at = datetime.fromisoformat(metadata['generated_at'])
    expiry_time = generated_at + timedelta(hours=CACHE_TTL_HOURS)
    return datetime.now(timezone.utc) < expiry_time


def get_cached_sitemap() -> Optional[str]:
    """Retrieve cached sitemap if valid."""
    if is_cache_valid() and os.path.exists(SITEMAP_CACHE_FILE):
        try:
            with open(SITEMAP_CACHE_FILE, 'r') as f:
                return f.read()
        except Exception:
            pass
    return None


def save_sitemap_to_cache(sitemap_xml: str):
    """Save sitemap to cache."""
    try:
        with open(SITEMAP_CACHE_FILE, 'w') as f:
            f.write(sitemap_xml)
        save_cache_metadata({
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'size': len(sitemap_xml)
        })
    except Exception as e:
        print(f"Failed to cache sitemap: {e}")


def generate_url_entry(loc: str, languages: list, priority: float = 0.5, changefreq: str = 'weekly') -> str:
    """Generate a single URL entry with hreflang annotations."""
    # Extract the path without language prefix
    path_parts = loc.split('/')
    if len(path_parts) > 1 and path_parts[1] in SUPPORTED_LANGUAGES:
        # Remove language prefix to get base path
        base_path = '/' + '/'.join(path_parts[2:]) if len(path_parts) > 2 else '/'
    else:
        base_path = loc
    
    entry = f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
"""
    
    # Add hreflang annotations for all languages
    for lang in languages:
        lang_url = f"{BASE_URL}/{lang}{base_path}" if base_path != '/' else f"{BASE_URL}/{lang}"
        entry += f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{lang_url}"/>\n'
    
    # Add x-default pointing to English
    default_url = f"{BASE_URL}/en{base_path}" if base_path != '/' else f"{BASE_URL}/en"
    entry += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{default_url}"/>\n'
    
    entry += "  </url>\n"
    return entry


async def generate_sitemap_xml(db) -> str:
    """Generate complete sitemap XML with all URLs."""
    
    # XML header
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
"""
    
    # Static pages with their priorities
    static_pages = [
        ('/', 1.0, 'daily'),           # Homepage
        ('/explore', 0.9, 'daily'),    # Explore page
        ('/about', 0.6, 'monthly'),    # About page
        ('/editorial-policy', 0.5, 'monthly'),  # Editorial policy
        ('/techniques', 0.7, 'weekly'),  # Techniques
    ]
    
    # Generate entries for static pages in all languages
    for page_path, priority, changefreq in static_pages:
        for lang in SUPPORTED_LANGUAGES:
            full_url = f"{BASE_URL}/{lang}{page_path}" if page_path != '/' else f"{BASE_URL}/{lang}"
            sitemap += generate_url_entry(full_url, SUPPORTED_LANGUAGES, priority, changefreq)
    
    # Fetch all published recipes from database
    try:
        recipes = await db.recipes.find(
            {"status": "published"},
            {"slug": 1, "date_fetched": 1, "average_rating": 1, "_id": 0}
        ).to_list(10000)
        
        # Sort by rating/date for priority calculation
        recipes_sorted = sorted(
            recipes, 
            key=lambda x: (x.get('average_rating', 0), x.get('date_fetched', '')),
            reverse=True
        )
        
        # Generate recipe URLs for all languages
        for idx, recipe in enumerate(recipes_sorted):
            slug = recipe.get('slug')
            if not slug:
                continue
            
            # Higher priority for top-rated recipes
            if idx < 10:
                priority = 0.9
            elif idx < 50:
                priority = 0.8
            elif idx < 100:
                priority = 0.7
            else:
                priority = 0.6
            
            for lang in SUPPORTED_LANGUAGES:
                recipe_url = f"{BASE_URL}/{lang}/recipe/{slug}"
                sitemap += generate_url_entry(recipe_url, SUPPORTED_LANGUAGES, priority, 'weekly')
    
    except Exception as e:
        print(f"Error fetching recipes for sitemap: {e}")
    
    # Fetch continents and countries for explore pages
    try:
        continents = await db.continents.find({}, {"slug": 1, "_id": 0}).to_list(100)
        
        for continent in continents:
            continent_slug = continent.get('slug')
            if not continent_slug:
                continue
            
            for lang in SUPPORTED_LANGUAGES:
                continent_url = f"{BASE_URL}/{lang}/explore/{continent_slug}"
                sitemap += generate_url_entry(continent_url, SUPPORTED_LANGUAGES, 0.8, 'weekly')
            
            # Fetch countries for this continent
            countries = await db.countries.find(
                {"continent_slug": continent_slug},
                {"slug": 1, "_id": 0}
            ).to_list(100)
            
            for country in countries:
                country_slug = country.get('slug')
                if not country_slug:
                    continue
                
                for lang in SUPPORTED_LANGUAGES:
                    country_url = f"{BASE_URL}/{lang}/explore/{continent_slug}/{country_slug}"
                    sitemap += generate_url_entry(country_url, SUPPORTED_LANGUAGES, 0.7, 'weekly')
    
    except Exception as e:
        print(f"Error fetching continents/countries for sitemap: {e}")
    
    # Close XML
    sitemap += "</urlset>"
    
    return sitemap


@router.get("/sitemap.xml")
async def get_sitemap(force_rebuild: bool = False):
    """
    Generate and serve the multilingual sitemap.
    
    - Uses cached version if available and valid (< 24 hours old)
    - Regenerates on-demand if cache expired or force_rebuild=true
    - Returns XML with proper Content-Type header
    """
    from server import db  # Import db from main server
    
    # Check cache first (unless force rebuild)
    if not force_rebuild:
        cached = get_cached_sitemap()
        if cached:
            return Response(
                content=cached,
                media_type="application/xml",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "X-Sitemap-Cached": "true"
                }
            )
    
    # Generate fresh sitemap
    sitemap_xml = await generate_sitemap_xml(db)
    
    # Cache it
    save_sitemap_to_cache(sitemap_xml)
    
    return Response(
        content=sitemap_xml,
        media_type="application/xml",
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Sitemap-Cached": "false"
        }
    )


@router.get("/sitemap-status")
async def get_sitemap_status():
    """Get sitemap cache status and metadata."""
    metadata = get_cache_metadata()
    cache_valid = is_cache_valid()
    
    return {
        "cached": cache_valid,
        "generated_at": metadata.get('generated_at'),
        "size_bytes": metadata.get('size'),
        "cache_ttl_hours": CACHE_TTL_HOURS,
        "supported_languages": SUPPORTED_LANGUAGES
    }
