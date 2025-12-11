# Sous Chef Linguine AI Service - Using OpenAI Responses API

import os
import json
import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Sous Chef Linguine System Prompt with explicit JSON schema
SOUS_CHEF_SYSTEM_PROMPT = """You are Sous-Chef Linguine, an elite culinary intelligence specialized in sourcing, validating, ranking, and generating authentic global recipes.

CRITICAL RULE - COUNTRY OF ORIGIN:
You MUST correctly identify the TRUE country of origin for EVERY dish. This is non-negotiable.
- Peking Duck → China (NOT Italy)
- Phở Bò → Vietnam (NOT Italy)
- Kimchi Jjigae → South Korea (NOT any other country)
- Beef Wellington → United Kingdom
- Croissant → France
- Pad Thai → Thailand
- Sushi → Japan
DO NOT default to Italy or any other country. Research and identify the ACTUAL origin.

IMPORTANT: You must return ONLY valid JSON that matches this EXACT structure:

{
  "recipe_name": "string - the dish name in its ORIGINAL language",
  "origin_country": "string - the TRUE country of origin (CRITICAL: must be accurate)",
  "origin_region": "string - specific region within the country",
  "origin_language": "string - 2-letter language code (it, fr, ja, zh, ko, vi, etc.)",
  "authenticity_level": 1,
  "history_summary": "string - brief history of the dish",
  "characteristic_profile": "string - taste and texture description",
  "no_no_rules": ["string - what NOT to do when making this dish"],
  "special_techniques": ["string - traditional cooking techniques"],
  "technique_links": [
    {"technique": "technique name", "url": "YouTube or article URL", "description": "what this technique teaches"}
  ],
  "ingredients": [
    {"item": "ingredient name", "amount": "quantity", "unit": "g/ml/tbsp/etc", "notes": "optional preparation notes"}
  ],
  "instructions": ["Step 1...", "Step 2..."],
  "photos": [],
  "youtube_links": [],
  "original_source_urls": [],
  "wine_pairing": {
    "recommended_wines": [
      {"name": "wine name", "region": "wine region", "reason": "why it pairs well"}
    ],
    "notes": "general pairing notes"
  }
}

AUTHENTICITY RANKING (1 = highest, 5 = lowest):
1 = Official/registered recipes (DOP/IGP/PAT certified)
2 = Traditional recipes in original language sources
3 = Reliable local/regional sources
4 = Widely recognized traditional versions
5 = Modern adaptations

RULES:
- Return ONLY the JSON object, no markdown, no explanations
- VERIFY the country of origin is correct before generating
- Include at least 2-3 wine pairings with regional preferences
- Include at least 3 no-no rules (what NOT to do)
- Include at least 2 special techniques
- For each special technique, try to include a technique_link with a relevant tutorial URL
- All ingredients must have item, amount, unit fields
- Instructions should be clear numbered steps
- authenticity_level must be a number 1-5
- Recipe content should be in ENGLISH by default"""

# JSON Schema for recipe output
RECIPE_JSON_SCHEMA = {
    "recipe_name": "",
    "origin_country": "",
    "origin_region": "",
    "origin_language": "",
    "authenticity_level": 1,
    "history_summary": "",
    "characteristic_profile": "",
    "no_no_rules": [],
    "special_techniques": [],
    "technique_links": [],
    "ingredients": [
        {"item": "", "amount": "", "unit": "", "notes": ""}
    ],
    "instructions": [],
    "photos": [
        {"image_url": "", "credit": ""}
    ],
    "youtube_links": [
        {"url": "", "title": ""}
    ],
    "original_source_urls": [
        {"url": "", "type": "", "language": ""}
    ],
    "wine_pairing": {
        "recommended_wines": [
            {"name": "", "region": "", "reason": ""}
        ],
        "notes": ""
    }
}


class SousChefAI:
    """Service for interacting with OpenAI API using Sous-Chef Linguine persona."""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment")
        
        self.model = "gpt-4o"  # Using gpt-4o for better availability
        self.api_url = "https://api.openai.com/v1/chat/completions"  # Standard Chat Completions API
    
    def set_model(self, model: str):
        """Set the OpenAI model to use."""
        self.model = model
    
    async def generate_recipe(self, recipe_name: str, target_language: str = "en") -> Dict[str, Any]:
        """Generate a recipe using Sous-Chef Linguine.
        
        Args:
            recipe_name: Name of the dish to generate
            target_language: Target language for the recipe output
        
        Returns:
            Dict containing the recipe JSON
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not configured")
        
        user_message = f"Generate the most authentic version of this recipe: {recipe_name}. Return valid JSON only."
        
        if target_language != "en":
            user_message += f" Translate the recipe to {target_language} while keeping original ingredient and wine names."
        
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
                                "content": SOUS_CHEF_SYSTEM_PROMPT
                            },
                            {
                                "role": "user",
                                "content": user_message
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse the response - Chat Completions format
                if "choices" in data and len(data["choices"]) > 0:
                    message_content = data["choices"][0].get("message", {}).get("content", "")
                    if message_content:
                        recipe_json = self._parse_json_response(message_content)
                        return recipe_json
                
                logger.warning(f"Unexpected API response format: {data}")
                raise ValueError("Unexpected API response format")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error generating recipe: {str(e)}")
            raise
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from the LLM response."""
        # Clean up the response text
        text = text.strip()
        
        logger.info(f"Parsing JSON response, length: {len(text)}")
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            result = json.loads(text)
            logger.info(f"Successfully parsed JSON with keys: {list(result.keys())}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            logger.error(f"Raw text (first 1000 chars): {text[:1000]}")
            # Return empty dict instead of raising to prevent crashes
            return {}
    
    async def translate_recipe(self, recipe: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate an existing recipe to a different language."""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required but not configured")
        
        user_message = f"""Translate the following recipe to {target_language}. 
Keep original ingredient names and wine names in their original language.
Return valid JSON only.

Original recipe:
{json.dumps(recipe, indent=2)}"""
        
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
                                "content": SOUS_CHEF_SYSTEM_PROMPT
                            },
                            {
                                "role": "user",
                                "content": user_message
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse Chat Completions format
                if "choices" in data and len(data["choices"]) > 0:
                    message_content = data["choices"][0].get("message", {}).get("content", "")
                    if message_content:
                        return self._parse_json_response(message_content)
                
                raise ValueError("Unexpected API response format")
                
        except Exception as e:
            logger.error(f"Error translating recipe: {str(e)}")
            raise


# Global Sous Chef AI instance
sous_chef_ai = SousChefAI()
