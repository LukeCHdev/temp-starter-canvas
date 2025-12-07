# Region Pydantic models

from pydantic import BaseModel
from typing import List

class Region(BaseModel):
    name: str
    slug: str
    description: str
    countries: List[str]
    image_url: str
    typical_characteristics: str
    created_at: str

class RegionCreate(BaseModel):
    name: str
    description: str
    countries: List[str]
