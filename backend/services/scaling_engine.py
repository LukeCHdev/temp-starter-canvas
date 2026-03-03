# Recipe scaling engine - Safe string-to-number parsing

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from fractions import Fraction

logger = logging.getLogger(__name__)


def parse_amount(amount_str: str) -> Tuple[Optional[float], bool]:
    """
    Safely parse an amount string to a float.
    
    Handles:
    - Integers: "380" → 380.0
    - Decimals: "1.5" → 1.5
    - Fractions: "1/2" → 0.5, "3/4" → 0.75
    - Mixed numbers: "1 1/2" → 1.5
    - Ranges: "2-3" → 2.5 (average)
    - Non-numeric: "to taste", "pinch" → None
    
    Returns:
        Tuple of (parsed_value, is_scalable)
        - parsed_value: float if parseable, None if not
        - is_scalable: True if the amount should be scaled
    """
    if not amount_str:
        return None, False
    
    amount_str = str(amount_str).strip().lower()
    
    # Non-scalable keywords
    non_scalable = ['to taste', 'pinch', 'dash', 'as needed', 'optional', 'some', 'few']
    for keyword in non_scalable:
        if keyword in amount_str:
            return None, False
    
    try:
        # Try direct float conversion first
        return float(amount_str), True
    except ValueError:
        pass
    
    # Try to parse fractions like "1/2", "3/4"
    fraction_match = re.match(r'^(\d+)/(\d+)$', amount_str)
    if fraction_match:
        num, denom = int(fraction_match.group(1)), int(fraction_match.group(2))
        if denom != 0:
            return num / denom, True
    
    # Try mixed numbers like "1 1/2" or "2 3/4"
    mixed_match = re.match(r'^(\d+)\s+(\d+)/(\d+)$', amount_str)
    if mixed_match:
        whole = int(mixed_match.group(1))
        num = int(mixed_match.group(2))
        denom = int(mixed_match.group(3))
        if denom != 0:
            return whole + (num / denom), True
    
    # Try ranges like "2-3" (return average)
    range_match = re.match(r'^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$', amount_str)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return (low + high) / 2, True
    
    # Try to extract leading number from strings like "2 large" or "3 medium"
    leading_num = re.match(r'^(\d+(?:\.\d+)?)', amount_str)
    if leading_num:
        return float(leading_num.group(1)), True
    
    # Cannot parse
    return None, False


def format_amount(value: float) -> str:
    """
    Format a scaled amount for display.
    
    Rules:
    - Whole numbers: "4" not "4.0"
    - Nice fractions: 0.5 → "1/2", 0.25 → "1/4", 0.75 → "3/4"
    - Otherwise: round to 1 decimal place
    """
    if value is None:
        return ""
    
    # Check if it's a whole number
    if value == int(value):
        return str(int(value))
    
    # Check for nice fractions
    nice_fractions = {
        0.25: "1/4",
        0.33: "1/3",
        0.5: "1/2",
        0.66: "2/3",
        0.67: "2/3",
        0.75: "3/4",
    }
    
    decimal_part = value - int(value)
    whole_part = int(value)
    
    for frac_val, frac_str in nice_fractions.items():
        if abs(decimal_part - frac_val) < 0.05:
            if whole_part == 0:
                return frac_str
            else:
                return f"{whole_part} {frac_str}"
    
    # Default: round to 1 decimal if needed, 2 for very small amounts
    if value < 1:
        return str(round(value, 2))
    return str(round(value, 1))


class ScalingEngine:
    """Engine for scaling recipe quantities."""
    
    # Default servings if not specified
    DEFAULT_SERVINGS = 4
    
    def scale_ingredients(self, ingredients: List[Dict], scale_factor: float) -> List[Dict]:
        """
        Scale a list of ingredients by the given factor.
        
        Args:
            ingredients: List of ingredient dicts with {item, amount, unit, notes}
            scale_factor: Multiplier (e.g., 2.0 for doubling)
        
        Returns:
            New list with scaled amounts (original list is not modified)
        """
        scaled = []
        
        for ing in ingredients:
            scaled_ing = ing.copy()
            
            amount_str = str(ing.get('amount', ''))
            parsed_value, is_scalable = parse_amount(amount_str)
            
            if is_scalable and parsed_value is not None:
                scaled_value = parsed_value * scale_factor
                scaled_ing['amount'] = format_amount(scaled_value)
                scaled_ing['_original_amount'] = amount_str
                scaled_ing['_scaled'] = True
            else:
                # Keep original amount for non-scalable items
                scaled_ing['_scaled'] = False
            
            scaled.append(scaled_ing)
        
        return scaled
    
    def scale_recipe(self, recipe_data: Dict[str, Any], target_servings: int) -> Dict[str, Any]:
        """
        Scale recipe to target servings.
        
        Args:
            recipe_data: Full recipe dict from database
            target_servings: Desired number of servings
        
        Returns:
            New recipe dict with scaled ingredients
        """
        # Get base servings - check multiple possible locations
        base_servings = (
            recipe_data.get('servings_default') or
            recipe_data.get('scaling_info', {}).get('base_servings') or
            recipe_data.get('servings') or
            self.DEFAULT_SERVINGS
        )
        
        # Ensure base_servings is valid
        try:
            base_servings = int(base_servings)
            if base_servings <= 0:
                base_servings = self.DEFAULT_SERVINGS
        except (ValueError, TypeError):
            base_servings = self.DEFAULT_SERVINGS
        
        # Calculate scale factor
        scale_factor = target_servings / base_servings
        
        # Create copy of recipe
        scaled_recipe = recipe_data.copy()
        
        # Scale main ingredients array (canonical schema)
        if 'ingredients' in scaled_recipe and isinstance(scaled_recipe['ingredients'], list):
            scaled_recipe['ingredients'] = self.scale_ingredients(
                scaled_recipe['ingredients'], 
                scale_factor
            )
        
        # Also handle translations if present - scale those ingredients too
        if 'translations' in scaled_recipe:
            scaled_translations = {}
            for lang, trans in scaled_recipe['translations'].items():
                if isinstance(trans, dict):
                    scaled_trans = trans.copy()
                    if 'ingredients' in trans and isinstance(trans['ingredients'], list):
                        scaled_trans['ingredients'] = self.scale_ingredients(
                            trans['ingredients'],
                            scale_factor
                        )
                    scaled_translations[lang] = scaled_trans
            scaled_recipe['translations'] = scaled_translations
        
        # Legacy support: scale authenticity_levels if present
        if 'authenticity_levels' in scaled_recipe:
            for level in scaled_recipe['authenticity_levels']:
                if 'ingredients' in level and isinstance(level['ingredients'], list):
                    level['ingredients'] = self.scale_ingredients(
                        level['ingredients'],
                        scale_factor
                    )
        
        # Add scaling metadata
        scaled_recipe['_scaling'] = {
            'base_servings': base_servings,
            'target_servings': target_servings,
            'scale_factor': round(scale_factor, 2),
            'scaled': True
        }
        
        return scaled_recipe


# Global scaling engine instance
scaling_engine = ScalingEngine()
