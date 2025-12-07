# Recipe generation service

import logging
from typing import Dict, Any
from datetime import datetime, timezone
from services.ai_service import ai_service
from utils.sous_chef_prompts import SOUS_CHEF_SYSTEM_PROMPT, RECIPE_GENERATION_PROMPT
from config.authenticity_levels import AUTHENTICITY_RANKS, get_classification_name

logger = logging.getLogger(__name__)

class RecipeGenerator:
    """Service for AI-powered recipe generation."""
    
    async def generate_recipe(self, dish_name: str, country: str, region: str) -> Dict[str, Any]:
        """Generate a complete recipe with authenticity validation."""
        
        # Context for logging
        context = {
            "country": country,
            "dish_name": dish_name,
            "region": region
        }
        
        user_prompt = f"""
Generate a complete, authentic recipe for "{dish_name}" from {country}.

Provide a JSON response with this exact structure:
{{
    "title_original": "Original dish name in native language",
    "title_translated": {{
        "en": "English translation",
        "it": "Italian translation",
        "es": "Spanish translation",
        "fr": "French translation"
    }},
    "original_language": "Language code (e.g., it, es, fr)",
    "original_country_domain": "Country domain (e.g., .it, .es, .fr)",
    "origin_story": "Rich, sensory narrative about the dish's origins",
    "cultural_background": "Emotional, warm description of cultural significance",
    "source_validation": {{
        "official_source": true/false,
        "native_language_validated": true/false,
        "country_domain_validated": true/false,
        "validation_notes": "Detailed validation notes",
        "authenticity_rank": 1, 2, or 3
    }},
    "source_references": [
        {{
            "source_type": "official" or "traditional" or "modern",
            "url": "Reference URL",
            "description": "Source description",
            "language": "Language of source",
            "domain": "Domain extension"
        }}
    ],
    "authenticity_levels": [
        {{
            "level": 1,
            "classification": "Traditional / Historical / Local Certified",
            "ingredients": [
                {{
                    "item": "Ingredient name",
                    "amount": 100,
                    "unit": "g",
                    "unit_metric": "100g",
                    "unit_imperial": "3.5oz",
                    "notes": "Sous Chef notes"
                }}
            ],
            "method": [
                {{
                    "step_number": 1,
                    "instruction": "Sensory, detailed instruction",
                    "timing": "5 minutes",
                    "temperature": {{
                        "celsius": 180,
                        "fahrenheit": 356
                    }}
                }}
            ],
            "differences": "What makes this level unique",
            "cultural_explanation": "Why this version exists"
        }}
    ],
    "tools_techniques": ["Tool 1", "Tool 2"],
    "notes": ["Note 1 in Sous Chef voice", "Note 2"],
    "substitutions": [
        {{
            "original_ingredient": "Original",
            "substitute": "Substitute",
            "cultural_justification": "Why this works",
            "authenticity_impact": "maintains" or "alters" or "breaks"
        }}
    ],
    "scaling_info": {{
        "base_servings": 4,
        "scalable": true,
        "scaling_notes": "Sous Chef scaling notes"
    }},
    "wine_pairing": {{
        "enabled": true,
        "suggestions": [
            {{
                "wine": "Wine name",
                "region": "Wine region",
                "justification": "Why this pairing"
            }}
        ]
    }},
    "related_dishes": [
        {{
            "dish_name": "Related dish",
            "recipe_slug": "related-dish-slug",
            "relationship": "starter" or "side" or "dessert"
        }}
    ]
}}

IMPORTANT:
- Use your warm, sensory Sous Chef Linguini voice
- Validate authenticity strictly
- Include at least levels 1 and 2
- All text should be rich, emotional, and sensory
"""
        
        try:
            # Generate recipe using AI with retry logic
            recipe_data = await ai_service.generate_json(
                system_message=SOUS_CHEF_SYSTEM_PROMPT,
                user_message=user_prompt,
                session_id=f"recipe_gen_{dish_name}_{country}",
                context=context
            )
            
            # Add metadata
            recipe_data['country'] = country
            recipe_data['region'] = region
            recipe_data['status'] = 'published'
            recipe_data['manual_override'] = False
            recipe_data['override_reason'] = ''
            recipe_data['created_at'] = datetime.now(timezone.utc).isoformat()
            recipe_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Generate slug
            recipe_data['slug'] = self._generate_slug(dish_name, country)
            
            # Generate SEO metadata
            recipe_data['seo_metadata'] = self._generate_seo_metadata(recipe_data)
            
            return recipe_data
        
        except Exception as e:
            logger.error(f"Recipe generation failed: {str(e)}")
            raise
    
    def _generate_slug(self, dish_name: str, country: str) -> str:
        """Generate URL-friendly slug."""
        slug = f"{dish_name}-{country}".lower()
        slug = slug.replace(' ', '-').replace('_', '-')
        # Remove special characters
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        return slug
    
    def _generate_seo_metadata(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO metadata."""
        title = recipe_data.get('title_translated', {}).get('en', recipe_data.get('title_original', ''))
        country = recipe_data.get('country', '')
        
        return {
            'meta_title': f"Authentic {title} Recipe from {country} | Sous Chef Linguini",
            'meta_description': recipe_data.get('origin_story', '')[:160],
            'keywords': [title, country, 'authentic recipe', 'traditional cooking'],
            'schema_json': {}
        }

# Global recipe generator instance
recipe_generator = RecipeGenerator()
