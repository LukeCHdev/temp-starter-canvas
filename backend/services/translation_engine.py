# Translation engine for locale adaptation

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TranslationEngine:
    """Engine for translating content to different locales."""
    
    def get_locale_content(self, recipe_data: Dict[str, Any], locale: str) -> Dict[str, Any]:
        """Get recipe content adapted to locale."""
        
        adapted_recipe = recipe_data.copy()
        
        # Determine language from locale
        lang = self._get_language_code(locale)
        
        # Get translated title
        title_translated = recipe_data.get('title_translated', {})
        if lang in title_translated:
            adapted_recipe['display_title'] = title_translated[lang]
        else:
            adapted_recipe['display_title'] = title_translated.get('en', recipe_data.get('title_original', ''))
        
        # Determine unit system
        unit_system = self._get_unit_system(locale)
        adapted_recipe['unit_system'] = unit_system
        
        return adapted_recipe
    
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
