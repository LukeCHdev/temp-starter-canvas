# Ingredient substitution engine

import logging
from typing import Dict, Any, List
from services.ai_service import ai_service
from utils.sous_chef_prompts import SOUS_CHEF_SYSTEM_PROMPT, SUBSTITUTION_PROMPT

logger = logging.getLogger(__name__)

class SubstitutionEngine:
    """Engine for suggesting ingredient substitutions."""
    
    async def suggest_substitutions(
        self, 
        ingredient: str, 
        recipe_name: str,
        recipe_context: str
    ) -> List[Dict[str, Any]]:
        """Suggest culturally appropriate substitutions."""
        
        user_prompt = f"""
Suggest culturally appropriate substitutions for "{ingredient}" in the recipe "{recipe_name}".

Recipe context:
{recipe_context}

Provide a JSON response with this structure:
{{
    "substitutions": [
        {{
            "substitute": "Substitute ingredient name",
            "cultural_justification": "Warm explanation of why this works",
            "authenticity_impact": "maintains" or "alters" or "breaks",
            "sensory_notes": "How the flavor/texture changes"
        }}
    ]
}}

Requirements:
- Only suggest substitutions that respect cultural integrity
- Use Sous Chef Linguini voice (warm, sensory)
- Rank authenticity impact honestly
- Provide 2-4 substitutions
"""
        
        try:
            result = await ai_service.generate_json(
                system_message=SOUS_CHEF_SYSTEM_PROMPT,
                user_message=user_prompt,
                session_id=f"substitution_{ingredient}_{recipe_name}"
            )
            
            return result.get('substitutions', [])
        
        except Exception as e:
            logger.error(f"Substitution generation failed: {str(e)}")
            raise

# Global substitution engine instance
substitution_engine = SubstitutionEngine()
