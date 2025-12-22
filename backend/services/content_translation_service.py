"""Content Translation Service - Async Recipe Translation with Storage

This service handles:
1. Translation queue management
2. Async translation via background worker
3. Translation status tracking per recipe/language
"""

import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ['en', 'es', 'it', 'fr', 'de']

TRANSLATION_SYSTEM_PROMPT = """You are a professional culinary translator. Your task is to translate recipe content while:

1. PRESERVING original proper nouns:
   - Wine names (e.g., "Frascati Superiore DOCG" stays as-is)
   - Original ingredient names in parentheses (e.g., "guanciale" can be noted)
   - Place names and regional terms

2. TRANSLATING these fields:
   - recipe_name: Translate the dish name naturally
   - history_summary: Full translation
   - characteristic_profile: Full translation  
   - no_no_rules: Full translation of each rule
   - special_techniques: Translate technique descriptions
   - instructions: Full translation of each step
   - ingredient notes: Translate preparation notes
   - wine_pairing.notes: Full translation
   - wine_pairing.recommended_wines[].reason: Full translation

3. OUTPUT: Return valid JSON matching the input structure exactly.
   Do not add or remove any fields.
   Do not add markdown formatting.
   Return ONLY the JSON object.
"""


class ContentTranslationService:
    """Service for translating recipe content and storing translations."""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found - translation will not work")
        
        self.model = "gpt-4o"
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    async def translate_recipe_content(self, recipe: Dict[str, Any], target_lang: str) -> Dict[str, Any]:
        """Translate recipe content to target language.
        
        Args:
            recipe: Original recipe document
            target_lang: Target language code (en, es, it, fr, de)
            
        Returns:
            Dict with translated content fields only (not full recipe)
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not configured")
        
        if target_lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_lang}")
        
        # Extract translatable content
        content_to_translate = {
            "recipe_name": recipe.get("recipe_name", ""),
            "history_summary": recipe.get("history_summary", ""),
            "characteristic_profile": recipe.get("characteristic_profile", ""),
            "no_no_rules": recipe.get("no_no_rules", []),
            "special_techniques": recipe.get("special_techniques", []),
            "instructions": recipe.get("instructions", []),
            "ingredients": recipe.get("ingredients", []),
            "wine_pairing": recipe.get("wine_pairing", {})
        }
        
        language_names = {
            'en': 'English',
            'es': 'Spanish', 
            'it': 'Italian',
            'fr': 'French',
            'de': 'German'
        }
        
        user_message = f"""Translate this recipe content to {language_names.get(target_lang, target_lang)}.
Return valid JSON only, no markdown:

{json.dumps(content_to_translate, indent=2, ensure_ascii=False)}"""
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": TRANSLATION_SYSTEM_PROMPT
                            },
                            {
                                "role": "user", 
                                "content": user_message
                            }
                        ],
                        "temperature": 0.3,  # Lower temp for more consistent translations
                        "max_tokens": 4000
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    message_content = data["choices"][0].get("message", {}).get("content", "")
                    if message_content:
                        translated = self._parse_json_response(message_content)
                        logger.info(f"Successfully translated recipe to {target_lang}")
                        return translated
                
                raise ValueError("Unexpected API response format")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error translating recipe: {str(e)}")
            raise
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from the LLM response."""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse translation JSON: {str(e)}")
            logger.error(f"Raw text (first 500 chars): {text[:500]}")
            raise ValueError(f"Invalid JSON response: {str(e)}")


# Global service instance
content_translation_service = ContentTranslationService()
