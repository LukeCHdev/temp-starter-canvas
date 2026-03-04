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
    
    def __init__(self):
        self.access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
        self._client = None
    
    @property
    def is_configured(self) -> bool:
        """Check if Unsplash API key is configured."""
        return bool(self.access_key)
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    def build_search_query(self, recipe: Dict[str, Any]) -> str:
        """
        Build an optimal search query for finding recipe images.
        
        Strategy:
        1. Use recipe name + country + "food" for best results
        2. Fall back to recipe name + "food" if no country
        3. Clean up query to avoid Unsplash API issues
        """
        title = recipe.get('recipe_name') or recipe.get('title_original') or 'food'
        country = recipe.get('origin_country') or recipe.get('country')
        
        # Build query
        if country:
            query = f"{title} {country} food"
        else:
            query = f"{title} food"
        
        # Clean up - remove special characters that might cause issues
        query = ' '.join(query.split())  # Normalize whitespace
        query = query[:100]  # Unsplash has query length limits
        
        return query
    
    def build_alt_text(self, recipe: Dict[str, Any]) -> str:
        """Build descriptive alt text for accessibility."""
        title = recipe.get('recipe_name') or recipe.get('title_original') or 'Recipe'
        country = recipe.get('origin_country') or recipe.get('country')
        
        if country:
            return f"Traditional {title} from {country}"
        return f"Traditional {title}"
    
    async def fetch_image(self, recipe: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Fetch an image from Unsplash for the given recipe.
        
        Returns:
            Dict with 'url', 'alt', 'source' keys if successful
            None if failed or no results
        """
        if not self.is_configured:
            logger.warning("Unsplash API key not configured")
            return None
        
        recipe_slug = recipe.get('slug', 'unknown')
        
        # Check in-memory lock to prevent duplicate concurrent fetches
        current_time = time.time()
        last_fetch = _fetch_locks.get(recipe_slug, 0)
        if current_time - last_fetch < _LOCK_TTL_SECONDS:
            logger.debug(f"Skipping fetch for {recipe_slug} - recent attempt in progress")
            return None
        
        # Set lock
        _fetch_locks[recipe_slug] = current_time
        
        try:
            query = self.build_search_query(recipe)
            logger.info(f"Fetching Unsplash image for: {recipe_slug} (query: {query})")
            
            client = await self.get_client()
            
            response = await client.get(
                self.UNSPLASH_API_URL,
                params={
                    'query': query,
                    'per_page': 1,
                    'orientation': 'landscape',  # Better for recipe cards
                    'content_filter': 'high',  # Safe content only
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
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                logger.info(f"No Unsplash results for: {query}")
                return None
            
            # Get the first result
            photo = results[0]
            
            # Use 'regular' size (1080px wide) - good balance of quality and load time
            image_url = photo.get('urls', {}).get('regular')
            
            if not image_url:
                return None
            
            # Build result
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
        finally:
            # Clear lock after TTL (let subsequent requests try again)
            # The lock will naturally expire based on timestamp comparison
            pass
    
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
