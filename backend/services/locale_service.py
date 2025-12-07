# Locale detection and management service

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LocaleService:
    """Service for detecting and managing user locale."""
    
    def detect_locale(self, browser_locale: str = None, geo_location: str = None) -> Dict[str, Any]:
        """Detect user locale and return localization settings."""
        
        # Default to English US
        locale = 'en-US'
        
        if browser_locale:
            locale = browser_locale
        
        # Determine language
        language = self._get_language(locale)
        
        # Determine unit systems
        units = self._get_units(locale)
        
        # Determine temperature system
        temperature_system = self._get_temperature_system(locale)
        
        return {
            'locale': locale,
            'language': language,
            'units': units,
            'temperature_system': temperature_system
        }
    
    def _get_language(self, locale: str) -> str:
        """Get language code from locale."""
        locale_lower = locale.lower()
        
        if 'it' in locale_lower:
            return 'it'
        elif 'es' in locale_lower:
            return 'es'
        elif 'fr' in locale_lower:
            return 'fr'
        elif 'de' in locale_lower:
            return 'de'
        elif 'ja' in locale_lower:
            return 'ja'
        else:
            return 'en'
    
    def _get_units(self, locale: str) -> str:
        """Get unit system (metric or imperial)."""
        locale_lower = locale.lower()
        
        if 'en-us' in locale_lower or 'en_us' in locale_lower:
            return 'imperial'
        else:
            return 'metric'
    
    def _get_temperature_system(self, locale: str) -> str:
        """Get temperature system (C or F)."""
        locale_lower = locale.lower()
        
        if 'en-us' in locale_lower or 'en_us' in locale_lower:
            return 'F'
        else:
            return 'C'

# Global locale service instance
locale_service = LocaleService()
