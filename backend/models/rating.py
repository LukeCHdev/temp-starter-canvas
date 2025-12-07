# Rating and Comment models

from pydantic import BaseModel
from typing import Optional

class RatingCreate(BaseModel):
    recipe_slug: str
    rating: int  # 1-5 stars
    comment: Optional[str] = None

class Rating(BaseModel):
    recipe_slug: str
    user_email: str
    rating: int
    comment: Optional[str] = None
    created_at: str
    updated_at: str

class CommentCreate(BaseModel):
    recipe_slug: str
    comment_text: str
    parent_comment_id: Optional[str] = None  # For replies

class Comment(BaseModel):
    recipe_slug: str
    user_email: str
    comment_text: str
    parent_comment_id: Optional[str] = None
    upvotes: int = 0
    created_at: str
    updated_at: str

class RecipeVerification(BaseModel):
    recipe_slug: str
    user_email: str
    verified: bool  # True = confirms authenticity
    notes: Optional[str] = None
    created_at: str
