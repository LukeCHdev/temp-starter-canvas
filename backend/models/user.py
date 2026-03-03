# User Pydantic models - Full Authentication System

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re

class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()

class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class User(BaseModel):
    """Full user model returned from API."""
    user_id: str
    email: EmailStr
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: Literal["local", "google"] = "local"
    provider_id: Optional[str] = None
    role: Literal["user", "admin", "moderator"] = "user"
    is_verified: bool = False
    created_at: str
    last_login: Optional[str] = None

class UserPublic(BaseModel):
    """Public user info (for reviews, etc.)."""
    user_id: str
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data extracted from token."""
    user_id: str
    email: str

class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth callback."""
    session_id: str

class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Model for confirming password reset."""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class EmailVerifyRequest(BaseModel):
    """Request model for email verification."""
    token: str

class SavedRecipe(BaseModel):
    """Model for saved/favorite recipes."""
    user_id: str
    recipe_slug: str
    saved_at: str

class AuthResponse(BaseModel):
    """Standard auth response."""
    success: bool
    message: str
    user: Optional[User] = None
