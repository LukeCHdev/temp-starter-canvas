"""
Authentication Routes - Secure User Authentication System

Supports:
- Email/Password registration and login
- Google OAuth via Emergent Auth
- HTTP-only cookie sessions
- Protected endpoints

REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4
import httpx
import logging
import os
import secrets

from models.user import (
    UserCreate, UserLogin, User, UserPublic,
    GoogleAuthRequest, PasswordResetRequest, PasswordResetConfirm,
    EmailVerifyRequest, AuthResponse
)
from utils.auth import hash_password, verify_password

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database reference (set by main app)
db: Optional[AsyncIOMotorDatabase] = None

# Rate limiting: IP -> list of timestamps
_login_attempts: dict = {}
_RATE_LIMIT_WINDOW = 300  # 5 minutes
_RATE_LIMIT_MAX = 10  # 10 attempts per window

def _check_rate_limit(ip: str):
    """Raise 429 if too many login attempts from this IP."""
    import time
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    # Prune old entries
    attempts = [ts for ts in attempts if now - ts < _RATE_LIMIT_WINDOW]
    if len(attempts) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    attempts.append(now)
    _login_attempts[ip] = attempts

def _get_client_ip(request: Request) -> str:
    """Get real client IP, accounting for proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# Session settings
SESSION_EXPIRE_DAYS = 7
COOKIE_NAME = "session_token"

# Emergent Auth endpoint
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

def set_auth_db(database: AsyncIOMotorDatabase):
    """Set the database reference for auth routes."""
    global db
    db = database

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return f"user_{uuid4().hex[:12]}"

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

async def get_session_user(request: Request) -> Optional[dict]:
    """
    Get the current user from session cookie.
    Returns None if not authenticated.
    """
    session_token = request.cookies.get(COOKIE_NAME)
    
    if not session_token:
        return None
    
    # Find session
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session:
        return None
    
    # Check expiry
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        # Session expired, clean up
        await db.user_sessions.delete_one({"session_token": session_token})
        return None
    
    # Get user
    user = await db.users.find_one(
        {"user_id": session["user_id"]},
        {"_id": 0, "password_hash": 0, "verification_token": 0, "reset_token": 0, "reset_token_expires": 0}
    )
    
    return user

async def require_auth(request: Request) -> dict:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated.
    """
    user = await get_session_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user

def set_session_cookie(response: Response, session_token: str):
    """Set the session cookie on the response."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=True,  # Required for SameSite=None
        samesite="none",  # Allow cross-site requests
        max_age=SESSION_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )

def clear_session_cookie(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=True,
        samesite="none"
    )

async def create_session(user_id: str) -> str:
    """Create a new session for a user."""
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    })
    
    # Update last login
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    return session_token


# ============================================
# REGISTRATION
# ============================================

@auth_router.post("/register")
async def register(user_data: UserCreate, response: Response):
    """
    Register a new user with email and password.
    
    Validates:
    - Email uniqueness
    - Username uniqueness
    - Password requirements
    - Password confirmation match
    """
    try:
        # Check passwords match
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Check if email exists
        existing_email = await db.users.find_one(
            {"email": user_data.email.lower()},
            {"_id": 0, "user_id": 1}
        )
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username exists
        existing_username = await db.users.find_one(
            {"username": user_data.username.lower()},
            {"_id": 0, "user_id": 1}
        )
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        user_id = generate_user_id()
        verification_token = secrets.token_urlsafe(32)
        
        user_doc = {
            "user_id": user_id,
            "email": user_data.email.lower(),
            "username": user_data.username.lower(),
            "password_hash": hash_password(user_data.password),
            "name": user_data.username,  # Default name to username
            "avatar_url": None,
            "provider": "local",
            "provider_id": None,
            "role": "user",
            "is_verified": False,
            "verification_token": verification_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None
        }
        
        await db.users.insert_one(user_doc)
        
        # Mock email verification - log to console
        logger.info(f"[EMAIL VERIFICATION] User: {user_data.email}")
        logger.info(f"[EMAIL VERIFICATION] Token: {verification_token}")
        logger.info(f"[EMAIL VERIFICATION] Link: /verify-email?token={verification_token}")
        
        # Create session and set cookie
        session_token = await create_session(user_id)
        set_session_cookie(response, session_token)
        
        # Return user data (without sensitive fields)
        user_doc.pop("password_hash", None)
        user_doc.pop("verification_token", None)
        user_doc.pop("_id", None)
        
        return {
            "success": True,
            "message": "Registration successful. Please check your email to verify your account.",
            "user": user_doc
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


# ============================================
# LOGIN
# ============================================

@auth_router.post("/login")
async def login(credentials: UserLogin, request: Request, response: Response):
    """
    Login with email and password.
    Sets HTTP-only session cookie on success.
    Rate-limited: max 10 attempts per 5 minutes per IP.
    """
    # Rate limit check
    client_ip = _get_client_ip(request)
    _check_rate_limit(client_ip)

    try:
        # Find user by email
        user = await db.users.find_one(
            {"email": credentials.email.lower()},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if this is a social-only account
        if user.get("provider") != "local" and not user.get("password_hash"):
            raise HTTPException(
                status_code=400,
                detail=f"This account uses {user.get('provider')} login. Please use that option."
            )
        
        # Verify password
        if not verify_password(credentials.password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session
        session_token = await create_session(user["user_id"])
        set_session_cookie(response, session_token)
        
        # Remove sensitive fields
        user.pop("password_hash", None)
        user.pop("verification_token", None)
        
        return {
            "success": True,
            "message": "Login successful",
            "user": user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


# ============================================
# LOGOUT
# ============================================

@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Logout the current user.
    Clears session cookie and deletes session from database.
    """
    session_token = request.cookies.get(COOKIE_NAME)
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    clear_session_cookie(response)
    
    return {"success": True, "message": "Logged out successfully"}


# ============================================
# GOOGLE OAUTH (Emergent Auth)
# ============================================

@auth_router.post("/social/google")
async def google_auth(auth_data: GoogleAuthRequest, response: Response):
    """
    Process Google OAuth callback via Emergent Auth.
    
    Flow:
    1. Frontend redirects to Emergent Auth
    2. User completes Google login
    3. Redirected back with session_id in URL fragment
    4. Frontend sends session_id to this endpoint
    5. We exchange session_id for user data
    6. Create/link user account and set session cookie
    """
    try:
        # Exchange session_id for user data from Emergent Auth
        async with httpx.AsyncClient() as client:
            headers = {"X-Session-ID": auth_data.session_id}
            resp = await client.get(EMERGENT_AUTH_URL, headers=headers)
            
            if resp.status_code != 200:
                logger.error(f"Emergent Auth error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=401, detail="Google authentication failed")
            
            google_data = resp.json()
        
        google_email = google_data.get("email", "").lower()
        google_name = google_data.get("name", "")
        google_picture = google_data.get("picture")
        google_id = google_data.get("id")
        
        if not google_email:
            raise HTTPException(status_code=400, detail="No email received from Google")
        
        # Check if user exists with this email
        existing_user = await db.users.find_one(
            {"email": google_email},
            {"_id": 0}
        )
        
        if existing_user:
            # Link Google to existing account if not already linked
            if existing_user.get("provider") == "local":
                await db.users.update_one(
                    {"user_id": existing_user["user_id"]},
                    {
                        "$set": {
                            "provider_id": google_id,
                            "avatar_url": google_picture or existing_user.get("avatar_url"),
                            "is_verified": True,  # Google verifies email
                            "last_login": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"Linked Google account to existing user: {google_email}")
            
            user_id = existing_user["user_id"]
            
            # Get updated user
            user = await db.users.find_one(
                {"user_id": user_id},
                {"_id": 0, "password_hash": 0, "verification_token": 0}
            )
        else:
            # Create new user
            user_id = generate_user_id()
            
            # Generate unique username from email
            base_username = google_email.split("@")[0].lower()
            base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-')[:20]
            username = base_username
            
            # Ensure username is unique
            counter = 1
            while await db.users.find_one({"username": username}):
                username = f"{base_username}{counter}"
                counter += 1
            
            user_doc = {
                "user_id": user_id,
                "email": google_email,
                "username": username,
                "name": google_name,
                "avatar_url": google_picture,
                "provider": "google",
                "provider_id": google_id,
                "password_hash": None,  # No password for social accounts
                "role": "user",
                "is_verified": True,  # Google verifies email
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": datetime.now(timezone.utc).isoformat()
            }
            
            await db.users.insert_one(user_doc)
            logger.info(f"Created new user via Google: {google_email}")
            
            user = {k: v for k, v in user_doc.items() if k not in ["password_hash", "_id"]}
        
        # Create session
        session_token = await create_session(user_id)
        set_session_cookie(response, session_token)
        
        return {
            "success": True,
            "message": "Google login successful",
            "user": user
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Google authentication failed")


# ============================================
# CURRENT USER
# ============================================

@auth_router.get("/me")
async def get_current_user(request: Request):
    """
    Get the currently authenticated user.
    Returns 401 if not authenticated.
    """
    user = await get_session_user(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "success": True,
        "user": user
    }


# ============================================
# EMAIL VERIFICATION (Mock)
# ============================================

@auth_router.post("/verify-email")
async def verify_email(data: EmailVerifyRequest):
    """
    Verify user email with token.
    (Mock implementation - logs to console)
    """
    try:
        user = await db.users.find_one(
            {"verification_token": data.token},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Mark as verified
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$set": {"is_verified": True},
                "$unset": {"verification_token": ""}
            }
        )
        
        logger.info(f"[EMAIL VERIFIED] User: {user['email']}")
        
        return {"success": True, "message": "Email verified successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Verification failed")


# ============================================
# PASSWORD RESET (Mock)
# ============================================

@auth_router.post("/reset-password")
async def request_password_reset(data: PasswordResetRequest):
    """
    Request a password reset email.
    (Mock implementation - logs to console)
    """
    try:
        user = await db.users.find_one(
            {"email": data.email.lower()},
            {"_id": 0}
        )
        
        # Always return success to prevent email enumeration
        if not user:
            return {"success": True, "message": "If an account exists, a reset email will be sent."}
        
        # Check if this is a social-only account
        if user.get("provider") != "local":
            return {"success": True, "message": "If an account exists, a reset email will be sent."}
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expires": reset_expires.isoformat()
                }
            }
        )
        
        # Mock email - log to console
        logger.info(f"[PASSWORD RESET] User: {data.email}")
        logger.info(f"[PASSWORD RESET] Token: {reset_token}")
        logger.info(f"[PASSWORD RESET] Link: /reset-password?token={reset_token}")
        
        return {"success": True, "message": "If an account exists, a reset email will be sent."}
    
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {"success": True, "message": "If an account exists, a reset email will be sent."}


@auth_router.post("/reset-password/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    """
    Reset password with token.
    """
    try:
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        user = await db.users.find_one(
            {"reset_token": data.token},
            {"_id": 0}
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Check token expiry
        expires = user.get("reset_token_expires")
        if expires:
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                raise HTTPException(status_code=400, detail="Reset token has expired")
        
        # Update password
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {
                "$set": {"password_hash": hash_password(data.new_password)},
                "$unset": {"reset_token": "", "reset_token_expires": ""}
            }
        )
        
        # Invalidate all sessions
        await db.user_sessions.delete_many({"user_id": user["user_id"]})
        
        logger.info(f"[PASSWORD RESET COMPLETE] User: {user['email']}")
        
        return {"success": True, "message": "Password reset successfully. Please login with your new password."}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirm error: {str(e)}")
        raise HTTPException(status_code=500, detail="Password reset failed")


# ============================================
# HELPER: Get Session User (for other routes)
# ============================================

async def get_optional_user(request: Request) -> Optional[dict]:
    """
    Get the current user if authenticated, else None.
    Does not raise an error if not authenticated.
    """
    return await get_session_user(request)
