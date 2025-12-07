# AI-powered translation service for recipes

import logging
from typing import Dict, Any
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

TRANSLATION_SYSTEM_PROMPT = """
You are a professional culinary translator specializing in recipe translation.

CRITICAL RULES:
1. Maintain Sous Chef Linguini's warm, emotional tone
2. Preserve culturally specific terms (add to glossary instead of translating)
3. Translate ingredient names accurately
4. Keep cooking techniques culturally authentic
5. Adapt units appropriately for target locale

TERMS TO PRESERVE (add to glossary, don't translate):
- Italian: soffritto, parmigiano, pecorino, mozzarella, al dente, ragù
- Spanish: mole, masa, salsa, tortilla, taco, enchilada
- French: roux, bouquet garni, mise en place, brunoise
- Japanese: dashi, miso, sake, mirin, umami, tempura
- Swedish: köttbullar, gravlax, surströmming

OUTPUT FORMAT:
Return a JSON object with:
{
  "translated_text": "full translation",
  "glossary_terms": ["term1", "term2"],
  "notes": "any translation notes"
}
"""

class AITranslationService:
    """AI-powered translation service for recipe content."""
    
    async def translate_recipe_field(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        field_type: str = "general"
    ) -> Dict[str, Any]:
        """Translate a recipe field using AI.
        
        Args:
            text: Text to translate
            source_lang: Source language code (it, es, fr, etc.)
            target_lang: Target language code
            field_type: Type of field (title, instruction, note, etc.)
        
        Returns:
            Dict with translated_text, glossary_terms, notes
        """
        
        if source_lang == target_lang:
            return {
                "translated_text": text,
                "glossary_terms": [],
                "notes": "No translation needed (same language)"
            }
        
        user_prompt = f"""
Translate this {field_type} from {source_lang} to {target_lang}:

TEXT TO TRANSLATE:
{text}

TARGET LANGUAGE: {target_lang}
FIELD TYPE: {field_type}

Remember:
- Keep warm, emotional Sous Chef Linguini tone
- Preserve culturally specific culinary terms
- Maintain authenticity and sensory descriptions
"""
        
        try:
            result = await ai_service.generate_json(
                system_message=TRANSLATION_SYSTEM_PROMPT,
                user_message=user_prompt,
                context={"source_lang": source_lang, "target_lang": target_lang, "field": field_type}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            # Fallback: return original text
            return {
                "translated_text": text,
                "glossary_terms": [],
                "notes": f"Translation failed: {str(e)}"
            }
    
    async def translate_full_recipe(
        self,
        recipe_data: Dict[str, Any],
        target_lang: str
    ) -> Dict[str, Any]:
        """Translate entire recipe to target language.
        
        This is computationally expensive, so use caching in production.
        """
        
        source_lang = recipe_data.get('original_language', 'en')
        
        if source_lang == target_lang:
            return recipe_data
        
        translated_recipe = recipe_data.copy()
        all_glossary_terms = []
        
        # Translate title (if not already available in title_translated)
        if target_lang not in recipe_data.get('title_translated', {}):
            title_result = await self.translate_recipe_field(
                recipe_data['title_original'],
                source_lang,
                target_lang,
                "title"
            )
            if 'title_translated' not in translated_recipe:
                translated_recipe['title_translated'] = {}
            translated_recipe['title_translated'][target_lang] = title_result['translated_text']
            all_glossary_terms.extend(title_result['glossary_terms'])
        
        # Translate origin story
        if recipe_data.get('origin_story'):
            origin_result = await self.translate_recipe_field(
                recipe_data['origin_story'],
                source_lang,
                target_lang,
                "origin_story"
            )
            translated_recipe[f'origin_story_{target_lang}'] = origin_result['translated_text']
            all_glossary_terms.extend(origin_result['glossary_terms'])
        
        # Translate cultural background
        if recipe_data.get('cultural_background'):
            cultural_result = await self.translate_recipe_field(
                recipe_data['cultural_background'],
                source_lang,
                target_lang,
                "cultural_background"
            )
            translated_recipe[f'cultural_background_{target_lang}'] = cultural_result['translated_text']
            all_glossary_terms.extend(cultural_result['glossary_terms'])
        
        # Store glossary
        translated_recipe['translation_glossary'] = list(set(all_glossary_terms))
        translated_recipe['translated_to'] = target_lang
        
        return translated_recipe

# Global AI translation service
ai_translation_service = AITranslationService()
