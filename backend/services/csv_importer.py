# CSV Import Service for Sous Chef Linguine

import csv
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from io import StringIO

logger = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Generate URL-friendly slug from text."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


class CSVImporter:
    """Service for importing recipes from CSV files."""
    
    # Required columns in CSV
    REQUIRED_COLUMNS = [
        'recipe_name',
        'origin_country',
        'origin_region',
        'origin_language',
        'authenticity_level'
    ]
    
    # Optional columns with defaults
    OPTIONAL_COLUMNS = {
        'history_summary': '',
        'characteristic_profile': '',
        'no_no_rules': '',  # Semicolon-separated
        'special_techniques': '',  # Semicolon-separated
        'ingredients': '',  # JSON string or semicolon-separated
        'instructions': '',  # Semicolon-separated
        'wine_name_1': '',
        'wine_region_1': '',
        'wine_reason_1': '',
        'wine_name_2': '',
        'wine_region_2': '',
        'wine_reason_2': '',
        'wine_name_3': '',
        'wine_region_3': '',
        'wine_reason_3': '',
        'wine_notes': '',
        'photo_url': '',
        'photo_credit': '',
        'youtube_url': '',
        'youtube_title': '',
        'source_url': '',
        'source_type': 'traditional',
        'source_language': ''
    }
    
    def parse_csv(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse CSV content and return list of recipe dictionaries.
        
        Args:
            csv_content: String containing CSV data
        
        Returns:
            List of recipe dictionaries ready for MongoDB insertion
        """
        recipes = []
        errors = []
        
        try:
            reader = csv.DictReader(StringIO(csv_content))
            
            # Validate required columns
            if reader.fieldnames:
                missing_cols = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
                if missing_cols:
                    raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                try:
                    recipe = self._parse_row(row)
                    recipes.append(recipe)
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    logger.warning(f"Error parsing row {row_num}: {str(e)}")
            
        except Exception as e:
            logger.error(f"CSV parsing error: {str(e)}")
            raise
        
        if errors:
            logger.warning(f"CSV import completed with {len(errors)} errors")
        
        return recipes
    
    def _parse_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a single CSV row into a recipe dictionary."""
        
        # Required fields
        recipe_name = row.get('recipe_name', '').strip()
        if not recipe_name:
            raise ValueError("recipe_name is required")
        
        origin_country = row.get('origin_country', '').strip()
        if not origin_country:
            raise ValueError("origin_country is required")
        
        # Generate slug
        slug = slugify(f"{recipe_name}-{origin_country}")
        
        # Parse list fields (semicolon-separated)
        no_no_rules = self._parse_list(row.get('no_no_rules', ''))
        special_techniques = self._parse_list(row.get('special_techniques', ''))
        instructions = self._parse_list(row.get('instructions', ''))
        
        # Parse ingredients
        ingredients = self._parse_ingredients(row.get('ingredients', ''))
        
        # Parse wine pairings
        wine_pairing = self._parse_wine_pairing(row)
        
        # Parse photos
        photos = []
        if row.get('photo_url'):
            photos.append({
                'image_url': row.get('photo_url', ''),
                'credit': row.get('photo_credit', '')
            })
        
        # Parse YouTube links
        youtube_links = []
        if row.get('youtube_url'):
            youtube_links.append({
                'url': row.get('youtube_url', ''),
                'title': row.get('youtube_title', '')
            })
        
        # Parse sources
        original_source_urls = []
        if row.get('source_url'):
            original_source_urls.append({
                'url': row.get('source_url', ''),
                'type': row.get('source_type', 'traditional'),
                'language': row.get('source_language', row.get('origin_language', ''))
            })
        
        # Build recipe document
        recipe = {
            'recipe_name': recipe_name,
            'slug': slug,
            'origin_country': origin_country,
            'origin_region': row.get('origin_region', '').strip(),
            'origin_language': row.get('origin_language', '').strip(),
            'authenticity_level': int(row.get('authenticity_level', 3)),
            'history_summary': row.get('history_summary', '').strip(),
            'characteristic_profile': row.get('characteristic_profile', '').strip(),
            'no_no_rules': no_no_rules,
            'special_techniques': special_techniques,
            'ingredients': ingredients,
            'instructions': instructions,
            'photos': photos,
            'youtube_links': youtube_links,
            'original_source_urls': original_source_urls,
            'wine_pairing': wine_pairing,
            'date_fetched': datetime.now(timezone.utc).isoformat(),
            'gpt_used': 'CSV Import',
            'collection_method': 'csv_import',
            'status': 'published'
        }
        
        return recipe
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse semicolon-separated string into list."""
        if not value:
            return []
        return [item.strip() for item in value.split(';') if item.strip()]
    
    def _parse_ingredients(self, value: str) -> List[Dict[str, str]]:
        """Parse ingredients from CSV.
        
        Expected format: "item1:amount1:unit1:notes1;item2:amount2:unit2:notes2"
        Or JSON format: '[{"item":"...","amount":"...","unit":"...","notes":"..."}]'
        """
        if not value:
            return []
        
        value = value.strip()
        
        # Try JSON format first
        if value.startswith('['):
            try:
                import json
                return json.loads(value)
            except:
                pass
        
        # Parse colon/semicolon format
        ingredients = []
        for item_str in value.split(';'):
            item_str = item_str.strip()
            if not item_str:
                continue
            
            parts = item_str.split(':')
            ingredient = {
                'item': parts[0].strip() if len(parts) > 0 else '',
                'amount': parts[1].strip() if len(parts) > 1 else '',
                'unit': parts[2].strip() if len(parts) > 2 else '',
                'notes': parts[3].strip() if len(parts) > 3 else ''
            }
            if ingredient['item']:
                ingredients.append(ingredient)
        
        return ingredients
    
    def _parse_wine_pairing(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse wine pairing from CSV row."""
        recommended_wines = []
        
        for i in range(1, 4):  # Up to 3 wines
            name = row.get(f'wine_name_{i}', '').strip()
            if name:
                recommended_wines.append({
                    'name': name,
                    'region': row.get(f'wine_region_{i}', '').strip(),
                    'reason': row.get(f'wine_reason_{i}', '').strip()
                })
        
        return {
            'recommended_wines': recommended_wines,
            'notes': row.get('wine_notes', '').strip()
        }


# Global CSV importer instance
csv_importer = CSVImporter()
