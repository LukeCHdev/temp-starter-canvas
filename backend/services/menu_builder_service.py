# Menu builder service

import logging
from typing import Dict, Any, List
from services.ai_service import ai_service
from utils.sous_chef_prompts import SOUS_CHEF_SYSTEM_PROMPT, MENU_BUILDER_PROMPT

logger = logging.getLogger(__name__)

class MenuBuilderService:
    """Service for AI-powered menu generation."""
    
    async def generate_menu(self, country: str, available_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a culturally coherent menu based on a country's recipes."""
        
        # Create recipe list for AI
        recipe_list = "\n".join([
            f"- {r.get('recipe_name', r.get('title_translated', {}).get('en', r.get('title_original', 'Unknown')))} ({r['slug']})"
            for r in available_recipes
        ])
        
        user_prompt = f"""
Create a culturally coherent 3-course menu for {country} cuisine.

Available recipes:
{recipe_list}

Provide a JSON response with this structure:
{{
    "menu_title": "Elegant menu name",
    "cultural_context": "Warm, sensory explanation of why these dishes pair well",
    "courses": [
        {{
            "course_type": "starter",
            "recipe_slug": "chosen-recipe-slug",
            "recipe_title": "Recipe Title",
            "pairing_justification": "Why this dish fits in the menu"
        }},
        {{
            "course_type": "main",
            "recipe_slug": "chosen-recipe-slug",
            "recipe_title": "Recipe Title",
            "pairing_justification": "Why this dish fits in the menu"
        }},
        {{
            "course_type": "dessert",
            "recipe_slug": "chosen-recipe-slug",
            "recipe_title": "Recipe Title",
            "pairing_justification": "Why this dish fits in the menu"
        }}
    ],
    "wine_pairing": "Optional wine pairing suggestion with Sous Chef voice"
}}

Requirements:
- All dishes must be from the same country
- Pairings must be culturally authentic
- Use warm, sensory Sous Chef Linguini voice
- Explain cultural harmony of the menu
"""
        
        try:
            menu_data = await ai_service.generate_json(
                system_message=SOUS_CHEF_SYSTEM_PROMPT,
                user_message=user_prompt,
                session_id=f"menu_builder_{country}"
            )
            
            menu_data['country'] = country
            
            return menu_data
        
        except Exception as e:
            logger.error(f"Menu generation failed: {str(e)}")
            raise

# Global menu builder service instance
menu_builder_service = MenuBuilderService()
