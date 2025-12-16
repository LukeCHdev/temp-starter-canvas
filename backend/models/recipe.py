# Recipe Pydantic models - CANONICAL SCHEMA for Sous-Chef Linguine
# This is the SINGLE SOURCE OF TRUTH for all recipe data

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============== CANONICAL RECIPE SCHEMA ==============
# This schema is enforced across:
# - AI generation (Sous-Chef Linguine GPT)
# - Admin JSON import
# - CSV import
# - Scraping & normalization
# - Future PDF import
#
# DO NOT create parallel or branching schemas.
# All recipes MUST conform to this structure.

class CanonicalIngredient(BaseModel):
    """Ingredient in the canonical recipe schema."""
    item: str = Field(..., description="Name of the ingredient")
    amount: str = Field(..., description="Quantity as string (e.g., '380', '1/2')")
    unit: str = Field(..., description="Unit of measurement (g, ml, tbsp, etc.)")
    notes: Optional[str] = Field("", description="Optional preparation notes")

class CanonicalWineRecommendation(BaseModel):
    """Wine pairing recommendation in the canonical schema."""
    name: str = Field(..., description="Wine name")
    region: str = Field(..., description="Wine region")
    reason: str = Field(..., description="Why this wine pairs well")

class CanonicalWinePairing(BaseModel):
    """Wine pairing section in the canonical schema."""
    recommended_wines: List[CanonicalWineRecommendation] = Field(default_factory=list)
    notes: Optional[str] = Field("", description="General pairing notes")

class CanonicalTechniqueLink(BaseModel):
    """Link to technique guide/tutorial. REQUIRED when special_techniques exist."""
    technique: str = Field(..., description="Name of the technique")
    url: str = Field(..., description="URL to tutorial (YouTube, article, etc.)")
    description: Optional[str] = Field("", description="Short description of what the link teaches")

class CanonicalPhoto(BaseModel):
    """Photo reference."""
    image_url: str
    credit: Optional[str] = ""

class CanonicalYouTubeLink(BaseModel):
    """YouTube video reference."""
    url: str
    title: Optional[str] = ""

class CanonicalSourceURL(BaseModel):
    """Source reference URL."""
    url: str
    type: Optional[str] = "traditional"  # official, traditional, modern, scraped
    language: Optional[str] = ""


class CanonicalRecipe(BaseModel):
    """
    CANONICAL RECIPE SCHEMA - Single Source of Truth
    
    This is the enforced schema for ALL recipes in the system.
    - AI generation MUST return this structure
    - Admin imports MUST validate against this
    - CSV imports MUST map to this
    - Scraping MUST normalize to this
    
    Translations are computed ON DEMAND and NOT saved as new recipes.
    """
    
    # ===== REQUIRED IDENTITY FIELDS =====
    recipe_name: str = Field(..., description="Name of the dish in its original language")
    origin_country: str = Field(..., description="Country of origin")
    origin_region: str = Field("", description="Specific region within the country")
    origin_language: str = Field("en", description="2-letter language code of dish's native language")
    authenticity_level: int = Field(3, ge=1, le=5, description="1=Official/DOP, 2=Traditional, 3=Regional, 4=Recognized, 5=Modern")
    
    # ===== REQUIRED CULTURAL CONTENT =====
    history_summary: str = Field("", description="Brief history of the dish")
    characteristic_profile: str = Field("", description="Taste and texture description")
    no_no_rules: List[str] = Field(default_factory=list, description="What NOT to do when making this dish")
    special_techniques: List[str] = Field(default_factory=list, description="Traditional cooking techniques")
    technique_links: List[CanonicalTechniqueLink] = Field(default_factory=list, description="Links to technique tutorials")
    
    # ===== REQUIRED RECIPE CONTENT =====
    ingredients: List[CanonicalIngredient] = Field(default_factory=list, description="List of ingredients")
    instructions: List[str] = Field(default_factory=list, description="Step-by-step cooking instructions")
    
    # ===== REQUIRED WINE PAIRING =====
    wine_pairing: Optional[CanonicalWinePairing] = Field(None, description="Wine pairing suggestions")
    
    # ===== OPTIONAL MEDIA =====
    photos: List[CanonicalPhoto] = Field(default_factory=list)
    youtube_links: List[CanonicalYouTubeLink] = Field(default_factory=list)
    original_source_urls: List[CanonicalSourceURL] = Field(default_factory=list)
    
    # ===== SYSTEM METADATA (auto-generated) =====
    slug: Optional[str] = Field("", description="URL-friendly identifier")
    continent: Optional[str] = Field("", description="Continent for categorization")
    content_language: str = Field("en", description="Language the content is written in")
    date_fetched: Optional[str] = Field("", description="When the recipe was added")
    gpt_used: Optional[str] = Field("Sous-Chef Linguine", description="AI model used")
    collection_method: Optional[str] = Field("ai_expansion", description="How recipe was collected")
    status: str = Field("published", description="published, draft, rejected")
    
    # ===== ANALYTICS (auto-managed) =====
    views_count: int = Field(0, description="Number of views")
    favorites_count: int = Field(0, description="Number of favorites")
    average_rating: float = Field(0, description="Average user rating")
    ratings_count: int = Field(0, description="Number of ratings")
    comments_count: int = Field(0, description="Number of comments")
    verifications_count: int = Field(0, description="Number of authenticity verifications")
    community_badge: Optional[str] = Field(None, description="Community awarded badge")
    
    @validator('authenticity_level')
    def validate_authenticity_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('authenticity_level must be between 1 and 5')
        return v
    
    @validator('origin_language')
    def validate_language_code(cls, v):
        if v and len(v) > 5:  # Allow codes like "en-US" or "zh-CN"
            raise ValueError('origin_language should be a 2-5 character language code')
        return v.lower() if v else "en"


def validate_canonical_recipe(data: dict) -> tuple[bool, list[str]]:
    """
    Validate a recipe dict against the canonical schema.
    Returns (is_valid, list_of_errors).
    
    Use this for:
    - Admin JSON imports
    - CSV imports
    - Scraping results
    - External data normalization
    """
    errors = []
    
    # Required fields
    required_fields = ['recipe_name']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate authenticity_level
    auth_level = data.get('authenticity_level')
    if auth_level is not None:
        if not isinstance(auth_level, int) or auth_level < 1 or auth_level > 5:
            errors.append("authenticity_level must be an integer between 1 and 5")
    
    # Validate ingredients structure
    ingredients = data.get('ingredients', [])
    if ingredients:
        for i, ing in enumerate(ingredients):
            if not isinstance(ing, dict):
                errors.append(f"ingredients[{i}] must be an object")
            elif not ing.get('item'):
                errors.append(f"ingredients[{i}].item is required")
    
    # Validate wine_pairing structure
    wine_pairing = data.get('wine_pairing')
    if wine_pairing and isinstance(wine_pairing, dict):
        wines = wine_pairing.get('recommended_wines', [])
        for i, wine in enumerate(wines):
            if isinstance(wine, dict):
                if not wine.get('name'):
                    errors.append(f"wine_pairing.recommended_wines[{i}].name is required")
    
    # Validate technique_links structure
    technique_links = data.get('technique_links', [])
    if technique_links:
        for i, link in enumerate(technique_links):
            if isinstance(link, dict):
                if not link.get('technique'):
                    errors.append(f"technique_links[{i}].technique is required")
                if not link.get('url'):
                    errors.append(f"technique_links[{i}].url is required")
    
    return (len(errors) == 0, errors)


def normalize_to_canonical(data: dict) -> dict:
    """
    Normalize a recipe dict to the canonical schema.
    Handles legacy fields and ensures proper structure.
    
    Use this to clean up:
    - Scraped data
    - Legacy imports
    - External JSON
    """
    normalized = {}
    
    # Map common field variations
    normalized['recipe_name'] = data.get('recipe_name') or data.get('title_original') or data.get('name') or ''
    normalized['origin_country'] = data.get('origin_country') or data.get('country') or ''
    normalized['origin_region'] = data.get('origin_region') or data.get('region') or ''
    normalized['origin_language'] = (data.get('origin_language') or data.get('original_language') or 'en')[:5].lower()
    normalized['authenticity_level'] = int(data.get('authenticity_level', 3))
    
    # Cultural content
    normalized['history_summary'] = data.get('history_summary') or data.get('origin_story') or ''
    normalized['characteristic_profile'] = data.get('characteristic_profile') or ''
    normalized['no_no_rules'] = data.get('no_no_rules') or []
    normalized['special_techniques'] = data.get('special_techniques') or data.get('tools_techniques') or []
    normalized['technique_links'] = data.get('technique_links') or []
    
    # Recipe content
    normalized['ingredients'] = _normalize_ingredients(data.get('ingredients', []))
    normalized['instructions'] = _normalize_instructions(data.get('instructions', []))
    
    # Wine pairing
    normalized['wine_pairing'] = _normalize_wine_pairing(data.get('wine_pairing'))
    
    # Media
    normalized['photos'] = data.get('photos') or []
    normalized['youtube_links'] = data.get('youtube_links') or []
    normalized['original_source_urls'] = data.get('original_source_urls') or data.get('source_references') or []
    
    # Copy through system fields if present
    for field in ['slug', 'continent', 'content_language', 'date_fetched', 'gpt_used', 
                  'collection_method', 'status', 'views_count', 'favorites_count',
                  'average_rating', 'ratings_count', 'comments_count']:
        if field in data:
            normalized[field] = data[field]
    
    return normalized


def _normalize_ingredients(ingredients: list) -> list:
    """Normalize ingredients to canonical format."""
    normalized = []
    for ing in ingredients:
        if isinstance(ing, dict):
            normalized.append({
                'item': str(ing.get('item', '')),
                'amount': str(ing.get('amount', '')),
                'unit': str(ing.get('unit', '')),
                'notes': str(ing.get('notes', ''))
            })
        elif isinstance(ing, str):
            # Handle string ingredients (legacy)
            normalized.append({
                'item': ing,
                'amount': '',
                'unit': '',
                'notes': ''
            })
    return normalized


def _normalize_instructions(instructions: list) -> list:
    """Normalize instructions to canonical format (list of strings)."""
    normalized = []
    for inst in instructions:
        if isinstance(inst, dict):
            # Handle legacy MethodStep format
            normalized.append(str(inst.get('instruction', '')))
        elif isinstance(inst, str):
            normalized.append(inst)
    return normalized


def _normalize_wine_pairing(wine_pairing) -> dict:
    """Normalize wine pairing to canonical format."""
    if not wine_pairing:
        return {'recommended_wines': [], 'notes': ''}
    
    if isinstance(wine_pairing, dict):
        wines = wine_pairing.get('recommended_wines') or wine_pairing.get('suggestions') or []
        normalized_wines = []
        for wine in wines:
            if isinstance(wine, dict):
                normalized_wines.append({
                    'name': wine.get('name') or wine.get('wine') or '',
                    'region': wine.get('region') or '',
                    'reason': wine.get('reason') or wine.get('justification') or ''
                })
        return {
            'recommended_wines': normalized_wines,
            'notes': wine_pairing.get('notes') or ''
        }
    
    return {'recommended_wines': [], 'notes': ''}


# ============== ALIASES FOR BACKWARD COMPATIBILITY ==============
# These point to the canonical models

SimpleIngredient = CanonicalIngredient
WineRecommendation = CanonicalWineRecommendation
SimpleWinePairing = CanonicalWinePairing
TechniqueLink = CanonicalTechniqueLink
Photo = CanonicalPhoto
YouTubeLink = CanonicalYouTubeLink
SourceURL = CanonicalSourceURL
SousChefRecipe = CanonicalRecipe
Recipe = CanonicalRecipe


# ============== API REQUEST MODELS ==============

class RecipeCreate(BaseModel):
    """Request model for creating/generating a recipe."""
    dish_name: str
    country: Optional[str] = None
    region: Optional[str] = None

class RecipeReject(BaseModel):
    """Request model for rejecting a recipe."""
    recipe_id: str
    rejection_reason: str
    validation_failures: List[str] = []

