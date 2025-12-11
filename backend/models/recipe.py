# Recipe Pydantic models - Updated for Sous-Chef Linguine GPT schema

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ============== SOUS-CHEF LINGUINE SCHEMA ==============
# This is the schema used by the Sous-Chef GPT and stored in MongoDB

class SimpleIngredient(BaseModel):
    """Ingredient as returned by Sous-Chef GPT"""
    item: str
    amount: str
    unit: str
    notes: Optional[str] = ""

class WineRecommendation(BaseModel):
    """Wine pairing recommendation"""
    name: str
    region: str
    reason: str

class SimpleWinePairing(BaseModel):
    """Wine pairing section"""
    recommended_wines: List[WineRecommendation] = []
    notes: Optional[str] = ""

class Photo(BaseModel):
    """Photo reference"""
    image_url: str
    credit: Optional[str] = ""

class YouTubeLink(BaseModel):
    """YouTube video reference"""
    url: str
    title: Optional[str] = ""

class SourceURL(BaseModel):
    """Source reference URL"""
    url: str
    type: Optional[str] = "traditional"
    language: Optional[str] = ""

class TechniqueLink(BaseModel):
    """Link to technique guide/tutorial"""
    technique: str
    url: str
    description: Optional[str] = ""

class SousChefRecipe(BaseModel):
    """
    Recipe model matching Sous-Chef Linguine GPT output.
    This is the primary schema for new recipes.
    """
    # Identity
    recipe_name: str
    slug: Optional[str] = ""
    origin_country: str
    origin_region: Optional[str] = ""
    origin_language: Optional[str] = "en"
    continent: Optional[str] = ""
    authenticity_level: int = 3
    
    # Cultural Content
    history_summary: Optional[str] = ""
    characteristic_profile: Optional[str] = ""
    no_no_rules: List[str] = []
    special_techniques: List[str] = []
    
    # Recipe Content
    ingredients: List[SimpleIngredient] = []
    instructions: List[str] = []
    
    # Media
    photos: List[Photo] = []
    youtube_links: List[YouTubeLink] = []
    
    # Sources
    original_source_urls: List[SourceURL] = []
    
    # Wine Pairing
    wine_pairing: Optional[SimpleWinePairing] = None
    
    # Metadata
    date_fetched: Optional[str] = ""
    gpt_used: Optional[str] = "Sous-Chef Linguine"
    collection_method: Optional[str] = "ai_expansion"
    status: str = "published"
    
    # Analytics
    views_count: int = 0
    favorites_count: int = 0
    average_rating: float = 0
    ratings_count: int = 0
    comments_count: int = 0
    verifications_count: int = 0
    community_badge: Optional[str] = None


# ============== LEGACY SCHEMA (for backward compatibility) ==============
# These models support the older, more complex recipe format

class Temperature(BaseModel):
    celsius: Optional[float] = None
    fahrenheit: Optional[float] = None

class LegacyIngredient(BaseModel):
    item: str
    amount: float
    unit: str
    unit_metric: str
    unit_imperial: str
    notes: Optional[str] = ""

class MethodStep(BaseModel):
    step_number: int
    instruction: str
    timing: Optional[str] = ""
    temperature: Optional[Temperature] = None

class AuthenticityLevel(BaseModel):
    level: int
    classification: str
    ingredients: List[LegacyIngredient]
    method: List[MethodStep]
    differences: str
    cultural_explanation: str

class SourceReference(BaseModel):
    source_type: str
    url: str
    description: str
    language: str
    domain: str

class SourceValidation(BaseModel):
    official_source: bool
    native_language_validated: bool
    country_domain_validated: bool
    validation_notes: str
    authenticity_rank: int

class Substitution(BaseModel):
    original_ingredient: str
    substitute: str
    cultural_justification: str
    authenticity_impact: str

class ScalingInfo(BaseModel):
    base_servings: int
    scalable: bool
    scaling_notes: str

class WineSuggestion(BaseModel):
    wine: str
    region: str
    justification: str

class LegacyWinePairing(BaseModel):
    enabled: bool
    suggestions: List[WineSuggestion] = []

class RelatedDish(BaseModel):
    dish_name: str
    recipe_slug: str
    relationship: str

class SEOMetadata(BaseModel):
    meta_title: str
    meta_description: str
    keywords: List[str]
    schema_json: Dict[str, Any] = {}

class LegacyRecipe(BaseModel):
    """Legacy recipe model - for backward compatibility with old data"""
    slug: str
    title_original: str
    title_translated: Dict[str, str]
    country: str
    region: str
    original_language: str
    original_country_domain: str
    source_validation: SourceValidation
    source_references: List[SourceReference]
    authenticity_levels: List[AuthenticityLevel]
    origin_story: str
    cultural_background: str
    tools_techniques: List[str]
    notes: List[str]
    substitutions: List[Substitution]
    scaling_info: ScalingInfo
    wine_pairing: LegacyWinePairing
    related_dishes: List[RelatedDish] = []
    seo_metadata: SEOMetadata
    status: str = "published"
    rejection_reason: Optional[str] = ""
    manual_override: bool = False
    override_reason: Optional[str] = ""
    created_at: str
    updated_at: str


# ============== API REQUEST MODELS ==============

class RecipeCreate(BaseModel):
    """Request model for creating/generating a recipe"""
    dish_name: str
    country: Optional[str] = None
    region: Optional[str] = None

class RecipeReject(BaseModel):
    """Request model for rejecting a recipe"""
    recipe_id: str
    rejection_reason: str
    validation_failures: List[str] = []


# Alias for backward compatibility
Recipe = SousChefRecipe
