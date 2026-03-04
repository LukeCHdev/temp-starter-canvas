"""Pydantic models for Techniques."""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum
import re


class Difficulty(str, Enum):
    beginner = "Beginner"
    intermediate = "Intermediate"
    advanced = "Advanced"


class TechniqueSection(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class TechniqueCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    slug: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=60)
    difficulty: Difficulty
    readTime: int = Field(..., gt=0)
    introduction: str = Field(..., min_length=1)
    sections: List[TechniqueSection] = Field(..., min_length=1)
    status: Optional[str] = "draft"

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None and not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("Slug must be URL-safe (lowercase alphanumeric with hyphens)")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ("draft", "published"):
            raise ValueError("Status must be 'draft' or 'published'")
        return v
