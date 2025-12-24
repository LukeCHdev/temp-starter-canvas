"""Content Translation Service - Async Recipe Translation with Emergent Integration

This service handles:
1. Translation queue management
2. Async translation via background worker
3. Translation status tracking per recipe/language

Uses emergentintegrations library for LLM calls.
"""

import os
import json
import logging
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

LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'it': 'Italian',
    'fr': 'French',
    'de': 'German'
}


class ContentTranslationService:
    """Service for translating recipe content using Emergent Integration."""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("No LLM API key found - translation will not work")
        
        self.model = "gpt-4o"
        self.provider = "openai"
    
    async def translate_recipe_content(self, recipe: Dict[str, Any], target_lang: str) -> Dict[str, Any]:
        """Translate recipe content to target language.
        
        Args:
            recipe: Original recipe document
            target_lang: Target language code (en, es, it, fr, de)
            
        Returns:
            Dict with translated content fields only (not full recipe)
        """
        if not self.api_key:
            raise ValueError("No LLM API key configured")
        
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
        
        # Create translation prompt
        target_language_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        user_prompt = f"""Translate the following recipe content to {target_language_name}.

Return the translation as valid JSON with the same structure.

Content to translate:
{json.dumps(content_to_translate, ensure_ascii=False, indent=2)}"""

        try:
            # Use emergentintegrations library
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"translation-{recipe.get('slug', 'unknown')}-{target_lang}",
                system_message=TRANSLATION_SYSTEM_PROMPT
            ).with_model(self.provider, self.model)
            
            user_message = UserMessage(text=user_prompt)
            response = await chat.send_message(user_message)
            
            # Parse the JSON response
            translated_content = self._parse_json_response(response)
            
            # Add metadata
            translated_content['status'] = 'ready'
            translated_content['translated_at'] = datetime.now(timezone.utc).isoformat()
            translated_content['source_lang'] = recipe.get('content_language', 'en')
            translated_content['target_lang'] = target_lang
            
            return translated_content
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Clean up the response
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        
        # Try to parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            import re
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError(f"Could not parse JSON from response: {text[:200]}...")


# Global instance
content_translation_service = ContentTranslationService()
