# Recipe generation service using Sous-Chef Linguine GPT

import logging
import re
from typing import Dict, Any
from datetime import datetime, timezone
from services.sous_chef_ai import sous_chef_ai

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Generate URL-friendly slug from text."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


class RecipeGenerator:
    """Service for AI-powered recipe generation using Sous-Chef Linguine GPT."""
    
    async def generate_recipe(self, dish_name: str, country: str = None, region: str = None) -> Dict[str, Any]:
        """Generate a complete recipe using Sous-Chef Linguine GPT.
        
        Args:
            dish_name: Name of the dish to generate
            country: Optional country hint
            region: Optional region hint
        
        Returns:
            Recipe dictionary ready for MongoDB insertion
        """
        logger.info(f"Generating recipe for '{dish_name}' (country: {country}, region: {region})")
        
        try:
            # Call Sous-Chef Linguine GPT
            recipe_json = await sous_chef_ai.generate_recipe(dish_name)
            
            # Enrich with metadata
            recipe_data = self._enrich_recipe(recipe_json, dish_name, country, region)
            
            logger.info(f"Recipe generated successfully: {recipe_data['slug']}")
            return recipe_data
        
        except Exception as e:
            logger.error(f"Recipe generation failed for '{dish_name}': {str(e)}")
            raise
    
    def _enrich_recipe(self, recipe_json: Dict[str, Any], dish_name: str, country: str = None, region: str = None) -> Dict[str, Any]:
        """Enrich the AI-generated recipe with additional metadata."""
        
        # Use AI-provided values or fallbacks
        recipe_name = recipe_json.get('recipe_name', dish_name)
        origin_country = recipe_json.get('origin_country', country or 'Unknown')
        origin_region = recipe_json.get('origin_region', region or 'Unknown')
        
        # Generate slug
        slug = slugify(f"{recipe_name}-{origin_country}")
        
        # Build the enriched recipe document
        recipe = {
            # Identity
            'recipe_name': recipe_name,
            'slug': slug,
            'origin_country': origin_country,
            'origin_region': origin_region,
            'origin_language': recipe_json.get('origin_language', 'en'),
            'authenticity_level': recipe_json.get('authenticity_level', 3),
            
            # Cultural Content
            'history_summary': recipe_json.get('history_summary', ''),
            'characteristic_profile': recipe_json.get('characteristic_profile', ''),
            'no_no_rules': recipe_json.get('no_no_rules', []),
            'special_techniques': recipe_json.get('special_techniques', []),
            'technique_links': recipe_json.get('technique_links', []),
            
            # Recipe Content
            'ingredients': recipe_json.get('ingredients', []),
            'instructions': recipe_json.get('instructions', []),
            
            # Media
            'photos': recipe_json.get('photos', []),
            'youtube_links': recipe_json.get('youtube_links', []),
            
            # Sources
            'original_source_urls': recipe_json.get('original_source_urls', []),
            
            # Wine Pairing
            'wine_pairing': recipe_json.get('wine_pairing', {
                'recommended_wines': [],
                'notes': ''
            }),
            
            # Metadata
            'date_fetched': datetime.now(timezone.utc).isoformat(),
            'gpt_used': 'Sous-Chef Linguine',
            'collection_method': 'ai_expansion',
            'status': 'published',
            
            # Analytics (initialize)
            'views_count': 0,
            'favorites_count': 0,
            'average_rating': 0,
            'ratings_count': 0,
            'comments_count': 0,
            'verifications_count': 0,
            'community_badge': None
        }
        
        return recipe
    
    async def translate_recipe(self, recipe: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate an existing recipe to a different language."""
        return await sous_chef_ai.translate_recipe(recipe, target_language)


# Global recipe generator instance
recipe_generator = RecipeGenerator()
