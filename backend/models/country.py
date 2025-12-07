# Country Pydantic models

from pydantic import BaseModel
from typing import List

class TypicalDish(BaseModel):
    name: str
    recipe_slug: str
    description: str

class Country(BaseModel):
    name: str
    slug: str
    region: str
    country_code: str
    language: str
    domain_extension: str
    typical_dishes: List[TypicalDish]
    culinary_description: str
    image_url: str
    created_at: str

class CountryCreate(BaseModel):
    name: str
    region: str
    country_code: str
    language: str
    domain_extension: str
