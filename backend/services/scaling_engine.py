# Recipe scaling engine

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScalingEngine:
    """Engine for scaling recipe quantities."""
    
    def scale_recipe(self, recipe_data: Dict[str, Any], target_servings: int) -> Dict[str, Any]:
        """Scale recipe to target servings."""
        
        base_servings = recipe_data.get('scaling_info', {}).get('base_servings', 4)
        
        if base_servings == 0:
            raise ValueError("Base servings cannot be zero")
        
        scale_factor = target_servings / base_servings
        
        scaled_recipe = recipe_data.copy()
        
        # Scale ingredients in all authenticity levels
        if 'authenticity_levels' in scaled_recipe:
            for level in scaled_recipe['authenticity_levels']:
                if 'ingredients' in level:
                    for ingredient in level['ingredients']:
                        if 'amount' in ingredient:
                            ingredient['amount'] = round(ingredient['amount'] * scale_factor, 2)
                            # Update unit strings
                            ingredient['unit_metric'] = f"{ingredient['amount']}{ingredient.get('unit', 'g')}"
                            # Simple imperial conversion (not perfect but functional)
                            imperial_amount = ingredient['amount'] * 0.035274 if ingredient.get('unit') == 'g' else ingredient['amount']
                            ingredient['unit_imperial'] = f"{round(imperial_amount, 1)}oz"
        
        # Add scaling note
        scaled_recipe['scaling_note'] = f"Recipe scaled from {base_servings} to {target_servings} servings"
        
        return scaled_recipe

# Global scaling engine instance
scaling_engine = ScalingEngine()
