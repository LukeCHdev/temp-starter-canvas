"""
Unsplash Image Service - Automatic Recipe Image Assignment

This service provides lazy image assignment for recipes:
1. When a recipe is requested and has no image
2. Fetch a relevant image from Unsplash
3. Save it to the database
4. Return the updated recipe

Features:
- Server-side only (API key never exposed)
- Rate-limit safe (only fetches on first view)
- Concurrent request protection
- Graceful error handling (never blocks recipe page)
"""

import os
import re
import httpx
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

# In-memory lock to prevent duplicate fetches under concurrent traffic
# Maps recipe_slug -> timestamp of last fetch attempt
_fetch_locks: Dict[str, float] = defaultdict(float)
_LOCK_TTL_SECONDS = 30  # Prevent re-fetch within 30 seconds


class UnsplashService:
    """Service for fetching images from Unsplash API."""
    
    UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
    
    # Geographic descriptors to strip for simplified fallback queries
    _GEO_PATTERNS = [
        r'\balla\s+\w+',       # "alla Milanese", "alla Romana"
        r'\bal\s+\w+',         # "al Forno"
        r'\bdel\s+\w+',        # "del Nonno"
        r'\bdella\s+\w+',      # "della Nonna"
        r'\bdi\s+\w+',         # "di Parma"
        r'\bfrom\s+\w+',       # "from Naples"
        r'\bstyle\b',
        r'\btradition\w*\b',
        r'\bauthentic\b',
        r'\bhomemade\b',
        r'\bclassic\b',
    ]
    
    def __init__(self):
        self.access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        self._client = None
        self._geo_regex = re.compile(
            '|'.join(self._GEO_PATTERNS), re.IGNORECASE
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if Unsplash API key is configured."""
        return bool(self.access_key)
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    def _clean(self, q: str) -> str:
        """Normalize whitespace and cap length."""
        return ' '.join(q.split())[:100]
    
    def _simplify_title(self, title: str) -> str:
        """Strip geographic/style descriptors to get the core dish name."""
        simplified = self._geo_regex.sub('', title).strip()
        simplified = ' '.join(simplified.split())
        return simplified if simplified else title
    
    def build_fallback_queries(self, recipe: Dict[str, Any]) -> list[str]:
        """
        Build an ordered list of search queries with decreasing specificity.
        
        Strategy (each step only if previous returned 0 results):
          1. Exact:      "{title} {country} food"
          2. Simplified:  "{main_dish} {country} food"  (geographic descriptors removed)
          3. Cuisine:     "{country} food"
        
        Duplicates are dropped so the API is never hit twice with the same query.
        """
        title = recipe.get('recipe_name') or recipe.get('title_original') or 'food'
        country = recipe.get('origin_country') or recipe.get('country') or ''
        
        queries: list[str] = []
        seen: set[str] = set()
        
        def _add(q: str):
            cleaned = self._clean(q)
            key = cleaned.lower()
            if key not in seen and cleaned:
                seen.add(key)
                queries.append(cleaned)
        
        # Step 1 – exact title + country
        if country:
            _add(f"{title} {country} food")
        else:
            _add(f"{title} food")
        
        # Step 2 – simplified title + country
        simplified = self._simplify_title(title)
        if simplified.lower() != title.lower():
            if country:
                _add(f"{simplified} {country} food")
            else:
                _add(f"{simplified} food")
        
        # Step 3 – cuisine-only fallback
        if country:
            _add(f"{country} food")
        
        return queries
    
    def build_alt_text(self, recipe: Dict[str, Any]) -> str:
        """Build descriptive alt text for accessibility."""
        title = recipe.get('recipe_name') or recipe.get('title_original') or 'Recipe'
        country = recipe.get('origin_country') or recipe.get('country')
        
        if country:
            return f"Traditional {title} from {country}"
        return f"Traditional {title}"
    
    async def _search_unsplash(self, query: str) -> Optional[dict]:
        """
        Execute a single Unsplash search.
        Returns the first photo dict or None.
        """
        client = await self.get_client()
        
        response = await client.get(
            self.UNSPLASH_API_URL,
            params={
                'query': query,
                'per_page': 1,
                'orientation': 'landscape',
                'content_filter': 'high',
            },
            headers={
                'Authorization': f'Client-ID {self.access_key}',
                'Accept-Version': 'v1'
            }
        )
        
        if response.status_code == 429:
            logger.warning("Unsplash rate limit reached")
            return None
        
        if response.status_code != 200:
            logger.error(f"Unsplash API error: {response.status_code}")
            return None
        
        results = response.json().get('results', [])
        return results[0] if results else None
    
    async def fetch_image(self, recipe: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Fetch an image from Unsplash using multi-step fallback.
        
        Fallback chain:
          1. "{title} {country} food"
          2. "{simplified_title} {country} food"
          3. "{country} food"
        
        Stops at the first query that returns a result.
        Never crashes, never retries infinitely, never exposes the API key.
        """
        if not self.is_configured:
            logger.warning("Unsplash API key not configured")
            return None
        
        recipe_slug = recipe.get('slug', 'unknown')
        
        # Concurrency lock
        current_time = time.time()
        last_fetch = _fetch_locks.get(recipe_slug, 0)
        if current_time - last_fetch < _LOCK_TTL_SECONDS:
            logger.debug(f"Skipping fetch for {recipe_slug} - recent attempt in progress")
            return None
        _fetch_locks[recipe_slug] = current_time
        
        try:
            queries = self.build_fallback_queries(recipe)
            logger.info(f"Fetching Unsplash image for {recipe_slug} — {len(queries)} fallback queries")
            
            photo = None
            matched_query = None
            
            for query in queries:
                logger.info(f"  Trying query: {query}")
                photo = await self._search_unsplash(query)
                if photo:
                    matched_query = query
                    break
            
            if not photo:
                logger.info(f"No Unsplash results for {recipe_slug} after {len(queries)} queries")
                return None
            
            image_url = photo.get('urls', {}).get('regular')
            if not image_url:
                return None
            
            logger.info(f"Image found for {recipe_slug} via query: {matched_query}")
            
            return {
                'url': image_url,
                'alt': self.build_alt_text(recipe),
                'source': 'unsplash',
                'unsplash_id': photo.get('id'),
                'photographer': photo.get('user', {}).get('name'),
                'photographer_url': photo.get('user', {}).get('links', {}).get('html'),
            }
        
        except httpx.TimeoutException:
            logger.warning(f"Unsplash request timeout for {recipe_slug}")
            return None
        except Exception as e:
            logger.error(f"Unsplash fetch error for {recipe_slug}: {str(e)}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Global service instance
unsplash_service = UnsplashService()


async def auto_assign_image(db, recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Automatically assign an image to a recipe if it doesn't have one.
    
    This function:
    1. Checks if recipe already has an image
    2. If not, fetches from Unsplash
    3. Saves to database
    4. Returns updated recipe
    
    IMPORTANT: This function never blocks or crashes - if image fetch fails,
    it simply returns the recipe without an image.
    
    Args:
        db: MongoDB database instance
        recipe: Recipe document from database
    
    Returns:
        Recipe document (possibly with new image data)
    """
    # Check if recipe already has an image
    existing_image = recipe.get('image_url')
    existing_photos = recipe.get('photos', [])
    
    # If already has image_url, return as-is
    if existing_image:
        return recipe
    
    # If has photos array with images, use that
    if existing_photos and len(existing_photos) > 0:
        first_photo = existing_photos[0]
        if isinstance(first_photo, dict) and first_photo.get('image_url'):
            return recipe
        elif isinstance(first_photo, str):
            return recipe
    
    # No image - try to fetch from Unsplash
    image_data = await unsplash_service.fetch_image(recipe)
    
    if image_data:
        # Update recipe in database
        update_fields = {
            'image_url': image_data['url'],
            'image_alt': image_data['alt'],
            'image_source': image_data['source'],
            'image_metadata': {
                'unsplash_id': image_data.get('unsplash_id'),
                'photographer': image_data.get('photographer'),
                'photographer_url': image_data.get('photographer_url'),
                'assigned_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            await db.recipes.update_one(
                {'slug': recipe['slug']},
                {'$set': update_fields}
            )
            
            # Update the recipe object to return
            recipe.update(update_fields)
            logger.info(f"Auto-assigned image to recipe: {recipe['slug']}")
        
        except Exception as e:
            logger.error(f"Failed to save image for {recipe['slug']}: {str(e)}")
            # Don't fail - just return recipe without image
    
    return recipe
