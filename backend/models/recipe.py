# Recipe Pydantic models

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Temperature(BaseModel):
    celsius: Optional[float] = None
    fahrenheit: Optional[float] = None

class Ingredient(BaseModel):
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
    ingredients: List[Ingredient]
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

class WinePairing(BaseModel):
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

class Recipe(BaseModel):
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
    wine_pairing: WinePairing
    related_dishes: List[RelatedDish] = []
    seo_metadata: SEOMetadata
    status: str = "published"
    rejection_reason: Optional[str] = ""
    manual_override: bool = False
    override_reason: Optional[str] = ""
    created_at: str
    updated_at: str

class RecipeCreate(BaseModel):
    dish_name: str
    country: str
    region: str

class RecipeReject(BaseModel):
    recipe_id: str
    rejection_reason: str
    validation_failures: List[str]
