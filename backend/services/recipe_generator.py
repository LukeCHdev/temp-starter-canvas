# Recipe generation service using Sous-Chef Linguine GPT

import logging
import re
import unicodedata
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from services.sous_chef_ai import sous_chef_ai

logger = logging.getLogger(__name__)


# Continent mapping for proper categorization
COUNTRY_TO_CONTINENT = {
    # Europe
    "Italy": "Europe", "France": "Europe", "Spain": "Europe", "Germany": "Europe",
    "United Kingdom": "Europe", "Greece": "Europe", "Portugal": "Europe", "Sweden": "Europe",
    "Norway": "Europe", "Denmark": "Europe", "Finland": "Europe", "Netherlands": "Europe",
    "Belgium": "Europe", "Austria": "Europe", "Switzerland": "Europe", "Poland": "Europe",
    "Czech Republic": "Europe", "Hungary": "Europe", "Romania": "Europe", "Bulgaria": "Europe",
    "Croatia": "Europe", "Serbia": "Europe", "Ireland": "Europe", "Scotland": "Europe",
    "Wales": "Europe", "Russia": "Europe", "Ukraine": "Europe", "Turkey": "Europe",
    
    # Asia
    "Japan": "Asia", "China": "Asia", "South Korea": "Asia", "North Korea": "Asia",
    "Vietnam": "Asia", "Thailand": "Asia", "Indonesia": "Asia", "Malaysia": "Asia",
    "Singapore": "Asia", "Philippines": "Asia", "India": "Asia", "Pakistan": "Asia",
    "Bangladesh": "Asia", "Sri Lanka": "Asia", "Nepal": "Asia", "Myanmar": "Asia",
    "Cambodia": "Asia", "Laos": "Asia", "Taiwan": "Asia", "Hong Kong": "Asia",
    
    # Americas
    "United States": "Americas", "USA": "Americas", "Mexico": "Americas", "Canada": "Americas",
    "Brazil": "Americas", "Argentina": "Americas", "Peru": "Americas", "Colombia": "Americas",
    "Chile": "Americas", "Venezuela": "Americas", "Ecuador": "Americas", "Cuba": "Americas",
    "Jamaica": "Americas", "Dominican Republic": "Americas", "Puerto Rico": "Americas",
    
    # Africa
    "Morocco": "Africa", "Egypt": "Africa", "Ethiopia": "Africa", "Nigeria": "Africa",
    "South Africa": "Africa", "Kenya": "Africa", "Ghana": "Africa", "Senegal": "Africa",
    "Tunisia": "Africa", "Algeria": "Africa", "Tanzania": "Africa",
    
    # Middle East
    "Lebanon": "Middle East", "Israel": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
    "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East", "UAE": "Middle East",
    "Jordan": "Middle East", "Syria": "Middle East", "Yemen": "Middle East", "Oman": "Middle East",
    "Kuwait": "Middle East", "Bahrain": "Middle East", "Qatar": "Middle East", "Palestine": "Middle East",
    
    # Oceania
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania", "Papua New Guinea": "Oceania",
}


def slugify(text: str) -> str:
    """Generate URL-friendly slug from text, properly handling Unicode characters."""
    # Normalize Unicode characters (NFD decomposition)
    text = unicodedata.normalize('NFKD', text)
    # Remove diacritics but keep base letters
    text = ''.join(c for c in text if not unicodedata.combining(c))
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove any character that's not alphanumeric or hyphen
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def get_continent(country: str) -> str:
    """Get continent for a country."""
    return COUNTRY_TO_CONTINENT.get(country, "Unknown")


class RecipeGenerator:
    """Service for AI-powered recipe generation using Sous-Chef Linguine GPT."""
    
    async def generate_recipe(self, dish_name: str, country: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
        """Generate a complete recipe using Sous-Chef Linguine GPT.
        
        Args:
            dish_name: Name of the dish to generate
            country: Optional country hint (AI's response takes priority)
            region: Optional region hint (AI's response takes priority)
        
        Returns:
            Recipe dictionary ready for MongoDB insertion
        """
        logger.info(f"Generating recipe for '{dish_name}' (country hint: {country}, region hint: {region})")
        
        try:
            # Call Sous-Chef Linguine GPT
            recipe_json = await sous_chef_ai.generate_recipe(dish_name)
            
            # Enrich with metadata - AI's country/region takes PRIORITY over hints
            recipe_data = self._enrich_recipe(recipe_json, dish_name, country, region)
            
            logger.info(f"Recipe generated successfully: {recipe_data['slug']} (country: {recipe_data['origin_country']})")
            return recipe_data
        
        except Exception as e:
            logger.error(f"Recipe generation failed for '{dish_name}': {str(e)}")
            raise
    
    def _enrich_recipe(self, recipe_json: Dict[str, Any], dish_name: str, country_hint: Optional[str] = None, region_hint: Optional[str] = None) -> Dict[str, Any]:
        """Enrich the AI-generated recipe with additional metadata.
        
        IMPORTANT: AI-provided country/region takes PRIORITY over hints.
        Only use hints as fallback if AI didn't provide the value.
        """
        
        # Get recipe name from AI or use dish name
        recipe_name = recipe_json.get('recipe_name', dish_name)
        
        # PRIORITY: AI's country > hint > Unknown
        # This fixes the issue where wrong hints override correct AI responses
        ai_country = recipe_json.get('origin_country', '').strip()
        origin_country = ai_country if ai_country else (country_hint or 'Unknown')
        
        # PRIORITY: AI's region > hint > Unknown  
        ai_region = recipe_json.get('origin_region', '').strip()
        origin_region = ai_region if ai_region else (region_hint or 'Unknown')
        
        # Get continent based on country
        continent = get_continent(origin_country)
        
        # Generate slug with better Unicode handling
        slug = slugify(f"{recipe_name}-{origin_country}")
        
        # Ensure slug is not empty
        if not slug:
            slug = slugify(dish_name) or 'unknown-recipe'
        
        # Build the enriched recipe document
        recipe = {
            # Identity
            'recipe_name': recipe_name,
            'slug': slug,
            'origin_country': origin_country,
            'origin_region': origin_region,
            'continent': continent,  # Add continent for Explore page
            'origin_language': recipe_json.get('origin_language', 'en'),  # Native language of the dish's country
            'content_language': 'en',  # Language the recipe content is written in (always English for generated)
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
