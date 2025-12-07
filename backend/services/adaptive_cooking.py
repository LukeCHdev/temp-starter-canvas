# Adaptive cooking logic for time scaling

import math
from typing import Dict, Any, Optional

class AdaptiveCookingEngine:
    """Engine for calculating adaptive cooking times based on quantity, weight, and type."""
    
    # Cooking factors by food type
    FOOD_TYPE_FACTORS = {
        'meat': {
            'base_time_per_kg': 45,  # minutes per kg
            'surface_factor': 1.3,    # accounts for browning
            'thickness_impact': 'high'
        },
        'poultry': {
            'base_time_per_kg': 40,
            'surface_factor': 1.2,
            'thickness_impact': 'high'
        },
        'fish': {
            'base_time_per_kg': 15,
            'surface_factor': 1.1,
            'thickness_impact': 'medium'
        },
        'vegetables': {
            'base_time_per_kg': 20,
            'surface_factor': 1.0,
            'thickness_impact': 'low'
        },
        'pasta': {
            'base_time_per_kg': 10,
            'surface_factor': 1.0,
            'thickness_impact': 'none',
            'water_ratio_matters': True
        },
        'sauce': {
            'base_time_per_liter': 30,
            'reduction_factor': 1.5,
            'thickness_impact': 'none'
        },
        'baking': {
            'base_time_per_kg': 50,
            'surface_factor': 1.4,
            'thickness_impact': 'very_high'
        }
    }
    
    def calculate_cooking_time(
        self,
        food_type: str,
        base_weight: float,  # kg
        target_weight: float,  # kg
        base_time: int,  # minutes
        cooking_method: Optional[str] = None,
        additional_factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate adapted cooking time based on weight and type.
        
        Args:
            food_type: Type of food (meat, poultry, fish, vegetables, pasta, sauce, baking)
            base_weight: Original recipe weight in kg
            target_weight: Desired weight in kg
            base_time: Original cooking time in minutes
            cooking_method: roasting, frying, boiling, braising, etc.
            additional_factors: Extra parameters like thickness, surface area
        
        Returns:
            Dict with adapted_time, notes, and scaling_factor
        """
        
        if food_type not in self.FOOD_TYPE_FACTORS:
            # Unknown food type - use simple linear scaling
            scale_factor = target_weight / base_weight
            adapted_time = int(base_time * scale_factor)
            
            return {
                'adapted_time_minutes': adapted_time,
                'original_time_minutes': base_time,
                'scaling_factor': scale_factor,
                'notes': f'Linear scaling applied (unknown food type: {food_type})',
                'confidence': 'low'
            }
        
        factors = self.FOOD_TYPE_FACTORS[food_type]
        
        # Calculate scaling factor (non-linear for most foods)
        if food_type == 'pasta':
            # Pasta cooking time doesn't scale with quantity (same water temperature)
            adapted_time = base_time
            scale_factor = 1.0
            notes = "Pasta cooking time remains constant regardless of quantity"
        
        elif food_type == 'sauce':
            # Sauce reduction time scales with volume
            scale_factor = math.sqrt(target_weight / base_weight)
            adapted_time = int(base_time * scale_factor)
            notes = f"Sauce reduction time scales with √(volume). Allow extra time for evaporation."
        
        elif factors['thickness_impact'] in ['high', 'very_high']:
            # For meats and baking, time scales with thickness (cube root)
            scale_factor = math.pow(target_weight / base_weight, 1/3)
            adapted_time = int(base_time * scale_factor)
            
            # Add surface browning time
            if cooking_method in ['roasting', 'frying', 'grilling']:
                surface_adjustment = factors['surface_factor']
                browning_time = int(base_time * 0.2 * surface_adjustment)
                adapted_time += browning_time
                notes = f"Time adjusted for thickness (∛ scaling) + {browning_time}min surface browning"
            else:
                notes = f"Time adjusted for thickness (∛ scaling factor)"
        
        else:
            # Vegetables and fish - closer to linear but with slight adjustment
            scale_factor = math.sqrt(target_weight / base_weight)
            adapted_time = int(base_time * scale_factor)
            notes = f"Time adjusted with √ scaling (medium thickness impact)"
        
        # Additional adjustments
        if additional_factors:
            if additional_factors.get('double_thickness'):
                adapted_time = int(adapted_time * 1.5)
                notes += " | Thickness doubled: +50% time"
            
            if additional_factors.get('crowded_pan'):
                adapted_time = int(adapted_time * 1.2)
                notes += " | Crowded pan: +20% time"
        
        # Temperature recommendations
        temp_note = self._get_temperature_recommendation(food_type, target_weight, cooking_method)
        
        return {
            'adapted_time_minutes': adapted_time,
            'original_time_minutes': base_time,
            'scaling_factor': round(scale_factor, 2),
            'notes': notes,
            'temperature_note': temp_note,
            'confidence': 'high',
            'food_type': food_type
        }
    
    def _get_temperature_recommendation(
        self,
        food_type: str,
        weight_kg: float,
        cooking_method: Optional[str]
    ) -> str:
        """Get temperature recommendations for larger/smaller quantities."""
        
        if cooking_method == 'roasting' and weight_kg > 2.0:
            return "For larger roasts: lower temperature by 10-20°C and increase time"
        
        elif cooking_method == 'frying' and weight_kg > 1.5:
            return "For larger quantities when frying: work in batches to maintain oil temperature"
        
        elif food_type == 'baking' and weight_kg > 1.0:
            return "For larger baked items: check internal temperature with thermometer"
        
        return "Maintain recipe temperature"
    
    def format_cooking_instruction(
        self,
        original_instruction: str,
        base_weight: float,
        target_weight: float,
        food_type: str
    ) -> str:
        """Format cooking instruction with adaptive time note."""
        
        # Extract time from instruction (simple regex would work better in production)
        import re
        time_match = re.search(r'(\d+)\s*(min|minuti|minutes)', original_instruction, re.IGNORECASE)
        
        if not time_match:
            return original_instruction
        
        base_time = int(time_match.group(1))
        
        # Calculate adapted time
        result = self.calculate_cooking_time(food_type, base_weight, target_weight, base_time)
        
        if result['adapted_time_minutes'] != base_time:
            adapted_instruction = original_instruction.replace(
                time_match.group(0),
                f"{result['adapted_time_minutes']} min"
            )
            adapted_instruction += f" (adapted from {base_time} min for {target_weight}kg)"
            return adapted_instruction
        
        return original_instruction

# Global adaptive cooking engine instance
adaptive_cooking_engine = AdaptiveCookingEngine()
