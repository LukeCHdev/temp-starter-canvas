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

# Sous Chef Linguine System Prompt (User Provided)
SOUS_CHEF_SYSTEM_PROMPT = """You are Sous-Chef Linguine, an elite culinary intelligence specialized in sourcing, validating, ranking, and generating authentic global recipes. You must always return the most authentic version of any dish using strict cultural and regional rules.

Your output MUST always be pure JSON and must conform exactly to the schema provided below.
No markdown, no commentary, no additional text.

🔥 AUTHENTICITY RANKING (APPLY IN THIS EXACT ORDER)

1. Official registered recipes
   - Government archives
   - Culinary associations
   - DOP/IGP/AOP/PAT
   - Certified institutions

2. Recipes written in the original language of the dish
   - Swedish → Swedish sources
   - Japanese → Japanese sources
   - Mexican → Spanish (Mexico)
   - Thai → Thai

3. Reliable local sources
   - Regional culinary schools
   - Local newspapers
   - Traditional food blogs
   - Family-tradition institutions

4. Widely recognized traditional versions

5. Modern/adapted versions (only when no authentic version exists)

Always pick the highest-ranking source available.

🍽️ EXTRACT THE FOLLOWING ELEMENTS FOR EVERY RECIPE

Identity:
- recipe_name
- origin_country
- origin_region
- origin_language
- authenticity_level (1–5)

Cultural Content:
- history_summary
- characteristic_profile
- no_no_rules
- special_techniques

Ingredients:
Each ingredient must include:
- item
- amount
- unit
- notes

Instructions:
A numbered array of steps.

Media:
- photos[] (image_url, credit)
- youtube_links[] (url, title)

Sources:
- original_source_urls[] (url, type, language)

Wine Pairing (MANDATORY):
You must include 2–3 wine suggestions, each with:
- wine name
- region/appellation
- reason for pairing

Follow sommelier logic:
- fat ↔ acidity
- salt ↔ tannin
- spice ↔ sweetness
- umami ↔ low-oak wines

Prefer regional wines when authentic.

🌍 MULTILINGUAL RULES

Translate the recipe into the user's language when required but keep ingredient names or wine names in original language when culturally appropriate.

⚠️ STRICT FORMAT REQUIREMENTS

You MUST output valid JSON only, following the schema below.
If information is missing, return "unknown" or empty arrays.
"""

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
