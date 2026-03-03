# Rating and Review models - Authentication Required

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ReviewCreate(BaseModel):
    """Model for creating a new review (authenticated users only)."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=2000, description="Optional review comment")

class ReviewUpdate(BaseModel):
    """Model for updating an existing review."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)

class Review(BaseModel):
    """Model for a recipe review."""
    id: str
    recipe_slug: str
    user_id: str
    username: str
    avatar_url: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

class ReviewsResponse(BaseModel):
    """Response model for getting reviews."""
    reviews: List[Review]
    total: int
    average_rating: float
    ratings_count: int
    user_review: Optional[Review] = None  # Current user's review if logged in

# Legacy models for backward compatibility
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
