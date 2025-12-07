# Translation engine for locale adaptation

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TranslationEngine:
    """Engine for translating content to different locales."""
    
    def get_locale_content(self, recipe_data: Dict[str, Any], locale: str) -> Dict[str, Any]:
        """Get recipe content adapted to user's selected language.
        
        IMPORTANT: Recipes are sourced in native language for authenticity,
        but displayed in user's chosen language for usability.
        Authenticity metadata is preserved internally.
        """
        
        adapted_recipe = recipe_data.copy()
        
        # Determine language from locale
        lang = self._get_language_code(locale)
        
        # Get translated title
        title_translated = recipe_data.get('title_translated', {})
        if lang in title_translated:
            adapted_recipe['display_title'] = title_translated[lang]
        else:
            adapted_recipe['display_title'] = title_translated.get('en', recipe_data.get('title_original', ''))
        
        # Determine unit system (metric vs imperial)
        unit_system = self._get_unit_system(locale)
        adapted_recipe['unit_system'] = unit_system
        
        # Determine temperature system (C vs F)
        temp_system = self._get_temperature_system(locale)
        adapted_recipe['temperature_system'] = temp_system
        
        # Add glossary for culturally specific terms
        adapted_recipe['glossary'] = self._generate_glossary(recipe_data, lang)
        
        # Preserve authenticity metadata
        adapted_recipe['_authenticity_metadata'] = {
            'original_language': recipe_data.get('original_language'),
            'original_country_domain': recipe_data.get('original_country_domain'),
            'sourced_in_native_language': True,
            'displayed_in_language': lang,
            'user_locale': locale
        }
        
        return adapted_recipe
    
    def _get_temperature_system(self, locale: str) -> str:
        """Get temperature system (C or F)."""
        locale_lower = locale.lower()
        
        if 'en-us' in locale_lower or 'en_us' in locale_lower:
            return 'F'
        else:
            return 'C'
    
    def _generate_glossary(self, recipe_data: Dict[str, Any], target_lang: str) -> Dict[str, str]:
        """Generate glossary for culturally specific terms that shouldn't be translated."""
        
        # Common untranslatable culinary terms by language
        preserve_terms = {
            'it': ['soffritto', 'parmigiano', 'pecorino', 'mozzarella', 'al dente', 'ragu', 'frittata'],
            'es': ['mole', 'masa', 'salsa', 'tortilla', 'taco', 'enchilada', 'chile'],
            'fr': ['roux', 'bouquet garni', 'mise en place', 'brunoise', 'julienne'],
            'ja': ['dashi', 'miso', 'sake', 'mirin', 'umami', 'tempura', 'teriyaki'],
            'sv': ['köttbullar', 'gravlax', 'surströmming'],
            'mx': ['masa harina', 'pozole', 'mole poblano']
        }
        
        glossary = {}
        original_lang = recipe_data.get('original_language', 'en')
        
        if original_lang in preserve_terms:
            # Check if these terms appear in the recipe
            recipe_text = str(recipe_data).lower()
            for term in preserve_terms[original_lang]:
                if term.lower() in recipe_text:
                    # Term should be preserved in original language
                    glossary[term] = f"Traditional {original_lang.upper()} term - preserved for authenticity"
        
        return glossary
    
    def _get_language_code(self, locale: str) -> str:
        """Extract language code from locale."""
        locale_lower = locale.lower()
        
        if locale_lower.startswith('it'):
            return 'it'
        elif locale_lower.startswith('es'):
            return 'es'
        elif locale_lower.startswith('fr'):
            return 'fr'
        elif locale_lower.startswith('de'):
            return 'de'
        elif locale_lower.startswith('ja'):
            return 'ja'
        else:
            return 'en'
    
    def _get_unit_system(self, locale: str) -> Dict[str, str]:
        """Get unit system based on locale."""
        locale_lower = locale.lower()
        
        if locale_lower.startswith(('en-us', 'en_us')):
            return {
                'weight': 'imperial',
                'volume': 'imperial',
                'temperature': 'F'
            }
        else:
            return {
                'weight': 'metric',
                'volume': 'metric',
                'temperature': 'C'
            }

# Global translation engine instance
translation_engine = TranslationEngine()
