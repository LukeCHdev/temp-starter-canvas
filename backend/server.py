from fastapi import FastAPI, APIRouter, HTTPException, Query, Security, UploadFile, File, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

# Import models
from models.recipe import Recipe, RecipeCreate, RecipeReject
from models.region import Region, RegionCreate
from models.country import Country, CountryCreate
from models.user import User, UserCreate, UserLogin, Token, SavedRecipe
from models.rating import Rating, RatingCreate, Comment, CommentCreate, RecipeVerification

# Import services
from services.recipe_generator import recipe_generator
from services.authenticity_engine import authenticity_engine
from services.menu_builder_service import menu_builder_service
from services.scaling_engine import scaling_engine
from services.substitution_engine import substitution_engine
from services.translation_engine import translation_engine
from services.locale_service import locale_service
from services.csv_importer import csv_importer
from services.auto_translation_service import auto_translation_service, auto_translate_recipe

# Import auth utilities
from utils.auth import hash_password, verify_password, create_access_token, get_current_user

# Import country normalization utilities
from utils.country_normalization import normalize_country, get_continent, COUNTRY_LABELS, is_valid_country

# Import admin routes
from routes.admin import admin_router

# Import document import routes
from routes.document_import import document_router

# Import translation routes
from routes.translation import translation_router, set_database as set_translation_db

# Import sitemap routes
from routes.sitemap import router as sitemap_router, set_sitemap_db

# Import search routes
from routes.search import search_router, set_search_db

# Import prerender routes
from routes.prerender import router as prerender_router
from services.prerender_service import set_prerender_db

# Import auth routes
from routes.auth import auth_router, set_auth_db, get_session_user, require_auth

# Import techniques routes
from routes.techniques import techniques_router, set_techniques_db

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Set database for translation routes
set_translation_db(db)

# Set database for sitemap routes
set_sitemap_db(db)

# Set database for search routes
set_search_db(db)

# Set database for auto-translation service
auto_translation_service.set_database(db)

# Set database for prerender service
set_prerender_db(db)

# Set database for auth routes
set_auth_db(db)

# Set database for techniques routes
set_techniques_db(db)

# Create the main app
app = FastAPI(title="Sous Chef Linguini API")

# Create API router
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== RECIPE ROUTES ==============

# In-memory rate limiter for search
_search_rate_limits = {}

def _check_search_rate_limit(client_ip: str, max_requests: int = 30, window_seconds: int = 600) -> bool:
    """Check if client IP has exceeded search rate limit. Returns True if allowed."""
    import time
    now = time.time()
    if client_ip not in _search_rate_limits:
        _search_rate_limits[client_ip] = []
    # Prune old entries
    _search_rate_limits[client_ip] = [t for t in _search_rate_limits[client_ip] if now - t < window_seconds]
    if len(_search_rate_limits[client_ip]) >= max_requests:
        return False
    _search_rate_limits[client_ip].append(now)
    return True


@api_router.get("/recipes/search")
async def search_recipes(
    request: Request,
    q: str = Query(..., min_length=2, max_length=80),
    lang: Optional[str] = "en",
    limit: int = Query(10, ge=1, le=50),
):
    """Search for recipes in the database. Read-only, no AI generation.

    Uses indexed regex matching on recipe_name, origin_country, and slug.
    Returns a list of matching recipes sorted by relevance (exact > partial).
    """
    # Rate limit: 30 searches per 10 minutes per IP
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    if not _check_search_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many searches. Please wait before trying again.")

    try:
        q_stripped = q.strip()
        q_escaped = re.escape(q_stripped)
        q_slug = re.escape(q_stripped.lower().replace(" ", "-"))

        # Build indexed query: match recipe_name, origin_country, or slug
        search_filter = {
            "status": "published",
            "$or": [
                {"recipe_name": {"$regex": q_escaped, "$options": "i"}},
                {"origin_country": {"$regex": q_escaped, "$options": "i"}},
                {"slug": {"$regex": q_slug, "$options": "i"}},
            ],
        }

        recipes = await db.recipes.find(search_filter, {"_id": 0}).limit(limit).to_list(limit)

        if recipes:
            # Sort: exact name matches first, then partial
            q_lower = q_stripped.lower()
            def sort_key(r):
                name = (r.get("recipe_name") or "").lower()
                if name == q_lower:
                    return 0  # exact match
                if name.startswith(q_lower):
                    return 1  # prefix match
                return 2  # partial match
            recipes.sort(key=sort_key)

            logger.info(f"Search '{q_stripped}': {len(recipes)} results")
            return {
                "found": True,
                "recipes": recipes,
                "total": len(recipes),
            }

        # No results
        logger.info(f"Search '{q_stripped}': 0 results")
        return {
            "found": False,
            "recipes": [],
            "suggestion": "No recipes found. Try browsing by country or continent.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error for '{q}': {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Search failed. Please try again.")

@api_router.get("/recipes")
async def get_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None
):
    """Get all recipes with pagination and filters."""
    query = {"status": "published"}
    
    if region:
        query["$or"] = [{"region": region}, {"origin_region": region}]
    if country:
        query["$or"] = [{"country": country}, {"origin_country": country}]
    if search:
        search_escaped = re.escape(search)
        query["$or"] = [
            {"recipe_name": {"$regex": search_escaped, "$options": "i"}},
            {"title_original": {"$regex": search_escaped, "$options": "i"}},
            {"title_translated.en": {"$regex": search_escaped, "$options": "i"}}
        ]
    
    skip = (page - 1) * limit
    
    recipes = await db.recipes.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.recipes.count_documents(query)
    
    return {
        "recipes": recipes,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

# ============== HOMEPAGE & EXPLORE ROUTES (must be before /{slug}) ==============

@api_router.get("/recipes/best")
async def get_best_recipe(lang: str = "en"):
    """Get the #1 best recipe worldwide based on rating > reviews > favorites."""
    recipe = await db.recipes.find_one(
        {"status": "published"},
        {"_id": 0},
        sort=[
            ("average_rating", -1),
            ("ratings_count", -1),
            ("favorites_count", -1)
        ]
    )
    
    if not recipe:
        return {"recipe": None}
    
    # Translations are already embedded in recipe.translations[lang]
    return {"recipe": recipe, "lang": lang}

@api_router.get("/recipes/featured")
async def get_featured_recipes(limit: int = 4, lang: str = "en", skip: int = 1):
    """Get top featured recipes. skip=1 excludes the #1 best (for homepage), skip=0 for explore."""
    capped_limit = min(limit, 300)
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).skip(skip).limit(capped_limit).to_list(capped_limit)
    
    # Translations are already embedded in recipe.translations[lang]
    return {"recipes": recipes, "lang": lang}

@api_router.get("/recipes/top-worldwide")
async def get_top_worldwide(limit: int = 10, lang: str = "en"):
    """Get top 10 recipes worldwide sorted by rating > reviews > favorites.
    If lang is provided, includes translation data for that language.
    """
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).limit(limit).to_list(limit)
    
    # Translations are already embedded in recipe.translations[lang]
    # No additional processing needed - frontend will access recipe.translations[lang]
    
    return {"recipes": recipes, "lang": lang}

@api_router.get("/recipes/by-continent/{continent}")
async def get_recipes_by_continent_name(continent: str, limit: int = 10):
    """Get top recipes from a continent."""
    continent_name = continent.replace("-", " ").title()
    
    recipes = await db.recipes.find(
        {"continent": continent_name, "status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).limit(limit).to_list(limit)
    
    return {
        "continent": continent_name,
        "recipes": recipes
    }

@api_router.get("/recipes/by-country/{country}")
async def get_recipes_by_country_name(country: str, limit: int = 50):
    """Get all recipes from a specific country with ranking."""
    country_name = country.replace("-", " ").title()
    
    # Get recipes sorted by rating
    recipes = await db.recipes.find(
        {"origin_country": {"$regex": f"^{country_name}$", "$options": "i"}, "status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).limit(limit).to_list(limit)
    
    # Get continent for breadcrumb
    continent = recipes[0].get("continent", "Unknown") if recipes else "Unknown"
    
    return {
        "country": country_name,
        "continent": continent,
        "recipes": recipes,
        "total": len(recipes)
    }

@api_router.get("/recipes/{slug}")
async def get_recipe(slug: str, lang: Optional[str] = "en"):
    """Get single recipe by slug with optional translation.
    
    If lang parameter differs from the recipe's content_language,
    the recipe will be translated on-the-fly (not saved to DB).
    
    AUTO-IMAGE: If recipe has no image, generates one via AI (GPT Image 1).
    """
    from services.sous_chef_ai import sous_chef_ai
    from services.ai_image_service import auto_assign_ai_image
    
    try:
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # AUTO-IMAGE: Assign AI-generated image if recipe doesn't have one
        recipe = await auto_assign_ai_image(db, recipe)
        
        # Normalize language code
        target_lang = lang.lower()[:2] if lang else "en"
        
        # Check if translation is needed
        content_lang = recipe.get("content_language", "en")[:2].lower()
        
        if target_lang != content_lang:
            logger.info(f"Translating recipe '{slug}' from {content_lang} to {target_lang}")
            try:
                translated_recipe = await sous_chef_ai.translate_recipe(recipe, target_lang)
                # Preserve original metadata including image
                translated_recipe["slug"] = recipe["slug"]
                translated_recipe["_translated"] = True
                translated_recipe["_original_lang"] = content_lang
                translated_recipe["_display_lang"] = target_lang
                # Preserve image data
                if recipe.get("image_url"):
                    translated_recipe["image_url"] = recipe["image_url"]
                    translated_recipe["image_alt"] = recipe.get("image_alt")
                    translated_recipe["image_source"] = recipe.get("image_source")
                return translated_recipe
            except Exception as e:
                logger.warning(f"Translation failed, returning canonical: {str(e)}")
        
        return recipe
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============== REVIEWS & RATINGS ==============

from models.rating import ReviewCreate, ReviewUpdate, Review, ReviewsResponse
from uuid import uuid4

@api_router.post("/recipes/{slug}/review")
async def create_review(slug: str, review: ReviewCreate, request: Request):
    """Create or update a review for a recipe.
    
    AUTHENTICATION REQUIRED.
    One review per user per recipe - if user has existing review, it will be updated.
    Rate limited: max 5 reviews per hour per user.
    """
    import html
    import time

    try:
        # Require authentication
        user = await get_session_user(request)
        if not user:
            raise HTTPException(
                status_code=401, 
                detail="You must be logged in to leave a review"
            )
        
        user_id = user["user_id"]
        username = user.get("username", "Anonymous")
        avatar_url = user.get("avatar_url")
        
        # Rate limit: max 5 reviews per hour per user
        one_hour_ago = datetime.now(timezone.utc).isoformat()[:-13]  # rough hour cutoff
        recent_count = await db.recipe_reviews.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": one_hour_ago}
        })
        if recent_count >= 5:
            raise HTTPException(status_code=429, detail="Too many reviews. Please wait before posting again.")
        
        # Verify recipe exists
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Sanitize comment (XSS prevention)
        sanitized_comment = html.escape(review.comment.strip()) if review.comment else None
        
        # Check if user already has a review for this recipe
        existing_review = await db.recipe_reviews.find_one(
            {"recipe_slug": slug, "user_id": user_id},
            {"_id": 0}
        )
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing_review:
            # Update existing review
            await db.recipe_reviews.update_one(
                {"recipe_slug": slug, "user_id": user_id},
                {
                    "$set": {
                        "rating": review.rating,
                        "comment": sanitized_comment,
                        "updated_at": now,
                        "username": username,
                        "avatar_url": avatar_url
                    }
                }
            )
            review_doc = {
                "id": existing_review["id"],
                "recipe_slug": slug,
                "user_id": user_id,
                "username": username,
                "avatar_url": avatar_url,
                "rating": review.rating,
                "comment": sanitized_comment,
                "created_at": existing_review["created_at"],
                "updated_at": now
            }
            logger.info(f"Updated review for {slug} by user {user_id}")
        else:
            # Create new review
            review_doc = {
                "id": str(uuid4()),
                "recipe_slug": slug,
                "user_id": user_id,
                "username": username,
                "avatar_url": avatar_url,
                "rating": review.rating,
                "comment": sanitized_comment,
                "created_at": now,
                "updated_at": None
            }
            await db.recipe_reviews.insert_one(review_doc)
            review_doc.pop('_id', None)
            logger.info(f"New review for {slug} by user {user_id}: {review.rating} stars")
        
        # Calculate new average rating
        all_reviews = await db.recipe_reviews.find(
            {"recipe_slug": slug},
            {"rating": 1, "_id": 0}
        ).to_list(10000)
        
        ratings = [r["rating"] for r in all_reviews]
        new_average = sum(ratings) / len(ratings) if ratings else 0
        new_count = len(ratings)
        
        # Update recipe with new rating stats
        await db.recipes.update_one(
            {"slug": slug},
            {
                "$set": {
                    "average_rating": round(new_average, 2),
                    "ratings_count": new_count,
                    "updated_at": now
                }
            }
        )
        
        return {
            "success": True,
            "review": review_doc,
            "average_rating": round(new_average, 2),
            "ratings_count": new_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/recipes/{slug}/reviews")
async def get_reviews(slug: str, request: Request, limit: int = 50, offset: int = 0):
    """Get all reviews for a recipe.
    
    Returns reviews sorted by newest first.
    If user is authenticated, also returns their review (if any).
    """
    try:
        # Verify recipe exists
        recipe = await db.recipes.find_one(
            {"slug": slug, "status": "published"},
            {"average_rating": 1, "ratings_count": 1, "_id": 0}
        )
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Get reviews with pagination
        reviews = await db.recipe_reviews.find(
            {"recipe_slug": slug},
            {"_id": 0}
        ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        # Get total count
        total = await db.recipe_reviews.count_documents({"recipe_slug": slug})
        
        # Check if current user has a review
        user_review = None
        user = await get_session_user(request)
        if user:
            user_review = await db.recipe_reviews.find_one(
                {"recipe_slug": slug, "user_id": user["user_id"]},
                {"_id": 0}
            )
        
        return {
            "reviews": reviews,
            "total": total,
            "average_rating": recipe.get("average_rating", 0),
            "ratings_count": recipe.get("ratings_count", 0),
            "user_review": user_review
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reviews for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/recipes/{slug}/review")
async def update_review(slug: str, review: ReviewUpdate, request: Request):
    """Update the current user's review for a recipe.
    
    AUTHENTICATION REQUIRED.
    """
    import html
    try:
        # Require authentication
        user = await get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="You must be logged in to update a review")
        
        user_id = user["user_id"]
        
        # Find existing review
        existing = await db.recipe_reviews.find_one(
            {"recipe_slug": slug, "user_id": user_id},
            {"_id": 0}
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="You haven't reviewed this recipe yet")
        
        # Build update document
        update_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if review.rating is not None:
            update_fields["rating"] = review.rating
        if review.comment is not None:
            update_fields["comment"] = html.escape(review.comment.strip()) if review.comment else None
        
        # Update review
        await db.recipe_reviews.update_one(
            {"recipe_slug": slug, "user_id": user_id},
            {"$set": update_fields}
        )
        
        # Recalculate average if rating changed
        if review.rating is not None:
            all_reviews = await db.recipe_reviews.find(
                {"recipe_slug": slug},
                {"rating": 1, "_id": 0}
            ).to_list(10000)
            
            ratings = [r["rating"] for r in all_reviews]
            new_average = sum(ratings) / len(ratings) if ratings else 0
            
            await db.recipes.update_one(
                {"slug": slug},
                {"$set": {"average_rating": round(new_average, 2)}}
            )
        
        # Get updated review
        updated_review = await db.recipe_reviews.find_one(
            {"recipe_slug": slug, "user_id": user_id},
            {"_id": 0}
        )
        
        logger.info(f"Updated review for {slug} by user {user_id}")
        
        return {"success": True, "review": updated_review}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/recipes/{slug}/review")
async def delete_review(slug: str, request: Request):
    """Delete the current user's review for a recipe.
    
    AUTHENTICATION REQUIRED.
    """
    try:
        # Require authentication
        user = await get_session_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="You must be logged in to delete a review")
        
        user_id = user["user_id"]
        
        # Find existing review
        existing = await db.recipe_reviews.find_one(
            {"recipe_slug": slug, "user_id": user_id},
            {"_id": 0}
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="You haven't reviewed this recipe")
        
        # Delete review
        await db.recipe_reviews.delete_one({"recipe_slug": slug, "user_id": user_id})
        
        # Recalculate average
        all_reviews = await db.recipe_reviews.find(
            {"recipe_slug": slug},
            {"rating": 1, "_id": 0}
        ).to_list(10000)
        
        ratings = [r["rating"] for r in all_reviews]
        new_average = sum(ratings) / len(ratings) if ratings else 0
        new_count = len(ratings)
        
        await db.recipes.update_one(
            {"slug": slug},
            {
                "$set": {
                    "average_rating": round(new_average, 2),
                    "ratings_count": new_count
                }
            }
        )
        
        logger.info(f"Deleted review for {slug} by user {user_id}")
        
        return {
            "success": True,
            "message": "Review deleted",
            "average_rating": round(new_average, 2),
            "ratings_count": new_count
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review for {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/recipes/generate")
async def generate_recipe(recipe_create: RecipeCreate):
    """Generate a new recipe using Sous-Chef Linguine GPT.
    
    After generation, automatically queues translations for all supported languages
    (fr, it, es, de) to ensure consistent multilingual coverage.
    """
    try:
        # Generate recipe
        recipe_data = await recipe_generator.generate_recipe(
            dish_name=recipe_create.dish_name,
            country=recipe_create.country,
            region=recipe_create.region
        )
        
        # Save to database
        await db.recipes.insert_one(recipe_data)
        
        # Get the recipe slug for translation queueing
        recipe_slug = recipe_data.get('slug')
        
        # AUTO-TRANSLATION: Queue translations for all supported languages
        if recipe_slug:
            translation_result = await auto_translate_recipe(recipe_slug, source_lang='en')
            logger.info(f"Auto-translation queued for {recipe_slug}: {translation_result}")
        
        # Remove _id before returning
        recipe_data.pop('_id', None)
        
        return {
            "message": "Recipe generated successfully by Sous-Chef Linguine",
            "recipe": recipe_data,
            "translations_queued": translation_result.get('queued_languages', []) if recipe_slug else []
        }
    
    except Exception as e:
        logger.error(f"Recipe generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/recipes/reject-invalid")
async def reject_invalid_recipe(recipe_reject: RecipeReject):
    """Reject an invalid recipe."""
    try:
        result = await db.recipes.update_one(
            {"slug": recipe_reject.recipe_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejection_reason": recipe_reject.rejection_reason,
                    "validation_failures": recipe_reject.validation_failures,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return {
            "status": "rejected",
            "reason": recipe_reject.rejection_reason
        }
    
    except Exception as e:
        logger.error(f"Recipe rejection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/recipes/country/{country}")
async def get_recipes_by_country(country: str):
    """Get all recipes from a specific country."""
    recipes = await db.recipes.find(
        {"country": country, "status": "published"},
        {"_id": 0}
    ).to_list(100)
    
    return {"recipes": recipes}

@api_router.get("/recipes/region/{region}")
async def get_recipes_by_region(region: str):
    """Get all recipes from a specific region."""
    recipes = await db.recipes.find(
        {"region": region, "status": "published"},
        {"_id": 0}
    ).to_list(100)
    
    return {"recipes": recipes}

# ============== CSV IMPORT ROUTES ==============

@api_router.post("/recipes/import/csv")
async def import_recipes_from_csv(file: UploadFile = File(...)):
    """Import recipes from a CSV file.
    
    CSV Format Required Columns:
    - recipe_name, origin_country, origin_region, origin_language, authenticity_level
    
    Optional Columns:
    - history_summary, characteristic_profile, no_no_rules, special_techniques
    - ingredients (format: "item:amount:unit:notes;item2:amount2:unit2:notes2")
    - instructions (semicolon-separated)
    - wine_name_1, wine_region_1, wine_reason_1 (up to 3 wines)
    - photo_url, photo_credit, youtube_url, youtube_title
    - source_url, source_type, source_language
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV file")
        
        # Read and decode CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        recipes = csv_importer.parse_csv(csv_content)
        
        if not recipes:
            raise HTTPException(status_code=400, detail="No valid recipes found in CSV")
        
        # Insert recipes into database
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for recipe in recipes:
            try:
                # Check if recipe already exists
                existing = await db.recipes.find_one({"slug": recipe["slug"]})
                if existing:
                    skipped_count += 1
                    continue
                
                # Insert recipe
                await db.recipes.insert_one(recipe)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Error importing {recipe.get('recipe_name', 'unknown')}: {str(e)}")
                logger.error(f"Error importing recipe: {str(e)}")
        
        return {
            "message": "CSV import completed",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors[:10]  # Limit errors returned
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/recipes/import/template")
async def get_csv_template():
    """Get a CSV template for recipe import."""
    template_headers = [
        "recipe_name",
        "origin_country",
        "origin_region",
        "origin_language",
        "authenticity_level",
        "history_summary",
        "characteristic_profile",
        "no_no_rules",
        "special_techniques",
        "ingredients",
        "instructions",
        "wine_name_1",
        "wine_region_1",
        "wine_reason_1",
        "wine_name_2",
        "wine_region_2",
        "wine_reason_2",
        "wine_notes",
        "photo_url",
        "photo_credit",
        "youtube_url",
        "youtube_title",
        "source_url",
        "source_type",
        "source_language"
    ]
    
    example_row = {
        "recipe_name": "Spaghetti alla Carbonara",
        "origin_country": "Italy",
        "origin_region": "Lazio",
        "origin_language": "it",
        "authenticity_level": "1",
        "history_summary": "A Roman pasta dish documented by traditional institutions...",
        "characteristic_profile": "Rich, salty, creamy texture with smoky guanciale and pecorino romano.",
        "no_no_rules": "Never use cream;Never use garlic or onion;Must use guanciale not pancetta",
        "special_techniques": "mantecatura (creaming with pasta water)",
        "ingredients": "Spaghetti:380:g:;Guanciale:150:g:cut into strips;Egg yolks:4::;Pecorino Romano:100:g:finely grated;Black pepper:to taste::freshly ground",
        "instructions": "Cook the guanciale until crisp;Mix yolks, egg, pecorino, and pepper;Cook pasta al dente;Combine pasta, guanciale, and egg mixture off heat using mantecatura;Serve immediately with more pecorino and pepper",
        "wine_name_1": "Frascati Superiore DOCG",
        "wine_region_1": "Lazio",
        "wine_reason_1": "High acidity cuts through egg and guanciale richness",
        "wine_name_2": "Verdicchio dei Castelli di Jesi DOC",
        "wine_region_2": "Marche",
        "wine_reason_2": "Fresh, mineral white balancing salt and fat",
        "wine_notes": "Central Italian whites are classic; light reds also work if not oaky.",
        "photo_url": "",
        "photo_credit": "Accademia Italiana della Cucina",
        "youtube_url": "",
        "youtube_title": "",
        "source_url": "https://www.accademiaitalianacucina.it",
        "source_type": "official",
        "source_language": "it"
    }
    
    return {
        "headers": template_headers,
        "example": example_row,
        "notes": {
            "no_no_rules": "Semicolon-separated list",
            "special_techniques": "Semicolon-separated list",
            "ingredients": "Format: item:amount:unit:notes separated by semicolons",
            "instructions": "Semicolon-separated steps",
            "authenticity_level": "1 (highest) to 5 (lowest)"
        }
    }

# ============== REGION ROUTES ==============

@api_router.get("/regions")
async def get_regions():
    """Get all regions."""
    regions = await db.regions.find({}, {"_id": 0}).to_list(100)
    return {"regions": regions}

@api_router.get("/regions/{slug}")
async def get_region(slug: str):
    """Get single region by slug."""
    region = await db.regions.find_one({"slug": slug}, {"_id": 0})
    
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return region

# ============== COUNTRY ROUTES ==============

@api_router.get("/countries")
async def get_countries(lang: str = "en"):
    """Get all countries that have at least one recipe.
    
    Returns deduplicated, canonical country list with localized labels.
    Aggregates by canonical English name, returns localized display label.
    
    Query params:
    - lang: Language for display labels (en, it, fr, es, de)
    """
    # Aggregate distinct countries from recipes collection
    pipeline = [
        {"$match": {"status": "published", "origin_country": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    # Aggregate by canonical name (handle Italia -> Italy etc.)
    canonical_counts = {}
    
    async for doc in db.recipes.aggregate(pipeline):
        raw_country = doc["_id"]
        if not raw_country:
            continue
        
        # Normalize to canonical English
        canonical = normalize_country(raw_country)
        
        if canonical in canonical_counts:
            canonical_counts[canonical] += doc["recipe_count"]
        else:
            canonical_counts[canonical] = doc["recipe_count"]
    
    # Build response with localized labels
    countries = []
    for canonical, count in canonical_counts.items():
        # Get localized label
        if canonical in COUNTRY_LABELS:
            localized = COUNTRY_LABELS[canonical].get(lang, canonical)
        else:
            localized = canonical
        
        countries.append({
            "canonical": canonical,  # English name for filtering/queries
            "name": localized,       # Localized display label
            "slug": canonical.lower().replace(" ", "-"),
            "recipe_count": count
        })
    
    # Sort by recipe count (descending), then name (ascending)
    countries.sort(key=lambda x: (-x["recipe_count"], x["canonical"]))
    
    return {"countries": countries, "language": lang}

@api_router.get("/countries/with-recipes")
async def get_countries_with_recipes(min_recipes: int = 1, lang: str = "en"):
    """Get all countries that have at least min_recipes recipes.
    
    Returns deduplicated, canonical countries with localized labels.
    """
    pipeline = [
        {"$match": {"status": "published", "origin_country": {"$exists": True, "$nin": [None, ""]}}},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$sort": {"recipe_count": -1, "_id": 1}}
    ]
    
    # Aggregate by canonical name
    canonical_counts = {}
    
    async for doc in db.recipes.aggregate(pipeline):
        raw_country = doc["_id"]
        if not raw_country:
            continue
        
        canonical = normalize_country(raw_country)
        
        if canonical in canonical_counts:
            canonical_counts[canonical] += doc["recipe_count"]
        else:
            canonical_counts[canonical] = doc["recipe_count"]
    
    # Filter by min_recipes and build response
    countries = []
    for canonical, count in canonical_counts.items():
        if count >= min_recipes:
            if canonical in COUNTRY_LABELS:
                localized = COUNTRY_LABELS[canonical].get(lang, canonical)
            else:
                localized = canonical
            
            countries.append({
                "canonical": canonical,
                "name": localized,
                "slug": canonical.lower().replace(" ", "-"),
                "recipe_count": count
            })
    
    countries.sort(key=lambda x: (-x["recipe_count"], x["canonical"]))
    
    return {"countries": countries, "min_recipes": min_recipes, "language": lang}

@api_router.get("/countries/{slug}")
async def get_country(slug: str):
    """Get single country by slug."""
    country = await db.countries.find_one({"slug": slug}, {"_id": 0})
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country

# ============== MENU BUILDER ROUTES ==============

@api_router.post("/menu-builder")
async def build_menu(country: str):
    """Generate a culturally coherent menu based on a country's recipes."""
    try:
        # Get available recipes from the selected country
        # Query by origin_country to match the recipe data model
        recipes = await db.recipes.find(
            {"origin_country": {"$regex": f"^{country}$", "$options": "i"}, "status": "published"},
            {"_id": 0}
        ).to_list(50)
        
        if len(recipes) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough recipes for {country}. Need at least 3."
            )
        
        # Generate menu
        menu = await menu_builder_service.generate_menu(country, recipes)
        
        # Cache menu
        menu['generated_at'] = datetime.now(timezone.utc).isoformat()
        await db.menus.insert_one(menu)
        
        # Remove MongoDB _id before returning (prevents ObjectId serialization error)
        menu.pop('_id', None)
        
        return menu
    
    except Exception as e:
        logger.error(f"Menu generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== AI UTILITIES ROUTES ==============

@api_router.post("/ai/substitute")
async def suggest_substitutions(
    ingredient: str,
    recipe_name: str,
    recipe_context: str
):
    """Suggest ingredient substitutions."""
    try:
        substitutions = await substitution_engine.suggest_substitutions(
            ingredient=ingredient,
            recipe_name=recipe_name,
            recipe_context=recipe_context
        )
        
        return {"substitutions": substitutions}
    
    except Exception as e:
        logger.error(f"Substitution error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/ai/scale")
async def scale_recipe(
    recipe_slug: str,
    target_servings: int = Query(..., ge=1, le=50, description="Target number of servings")
):
    """Scale a recipe's ingredients to target servings.
    
    Returns the recipe with scaled ingredient amounts.
    Handles string amounts, fractions, and non-scalable items gracefully.
    """
    try:
        recipe = await db.recipes.find_one({"slug": recipe_slug}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Scale the recipe
        scaled_recipe = scaling_engine.scale_recipe(recipe, target_servings)
        
        return {
            "success": True,
            "recipe": scaled_recipe,
            "scaling": scaled_recipe.get('_scaling', {})
        }
    
    except ValueError as e:
        logger.error(f"Scaling validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Scaling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== LOCALE ROUTES ==============

@api_router.post("/locale/detect")
async def detect_locale(browser_locale: Optional[str] = None, geo_location: Optional[str] = None):
    """Detect user locale and return settings."""
    locale_settings = locale_service.detect_locale(browser_locale, geo_location)
    return locale_settings

# ============== AUTO-TRANSLATION ADMIN ROUTES ==============

@api_router.post("/admin/translations/backfill")
async def backfill_translations(limit: int = 100):
    """Backfill translations for existing recipes that are missing translations.
    
    This endpoint queues translation jobs for all recipes that don't have
    ready translations in all supported languages (fr, it, es, de).
    
    Use this to ensure all existing content has multilingual coverage.
    """
    try:
        result = await auto_translation_service.ensure_all_recipes_have_translations(limit=limit)
        return {
            "success": result['success'],
            "recipes_processed": result.get('recipes_processed', 0),
            "translations_queued": result.get('translations_queued', 0),
            "message": f"Queued {result.get('translations_queued', 0)} translation jobs"
        }
    except Exception as e:
        logger.error(f"Backfill error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/translations/queue-recipe/{slug}")
async def queue_recipe_translations(slug: str):
    """Manually queue translations for a specific recipe.
    
    Use this to re-queue translations for a recipe that may have failed
    or needs to be updated.
    """
    try:
        result = await auto_translate_recipe(slug, source_lang='en')
        return result
    except Exception as e:
        logger.error(f"Queue translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== AUTHENTICATION ROUTES ==============
# NOTE: Auth routes are now in routes/auth.py with HTTP-only cookie support
# The old JWT-based routes have been removed

# ============== FAVORITES ROUTES ==============

@api_router.post("/recipes/{recipe_slug}/favorite")
async def favorite_recipe(recipe_slug: str, request: Request):
    """Add a recipe to the current user's favorites."""
    from routes.auth import require_auth
    user = await require_auth(request)

    recipe = await db.recipes.find_one({"slug": recipe_slug, "status": "published"})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    existing = await db.favorites.find_one({
        "user_id": user["user_id"],
        "recipe_slug": recipe_slug
    })
    if existing:
        return {"success": True, "favorited": True}

    await db.favorites.insert_one({
        "user_id": user["user_id"],
        "recipe_slug": recipe_slug,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {"success": True, "favorited": True}


@api_router.delete("/recipes/{recipe_slug}/favorite")
async def unfavorite_recipe(recipe_slug: str, request: Request):
    """Remove a recipe from the current user's favorites."""
    from routes.auth import require_auth
    user = await require_auth(request)

    await db.favorites.delete_one({
        "user_id": user["user_id"],
        "recipe_slug": recipe_slug
    })

    return {"success": True, "favorited": False}


@api_router.get("/recipes/{recipe_slug}/favorite-status")
async def get_favorite_status(recipe_slug: str, request: Request):
    """Check if the current user has favorited a recipe. Returns false for guests."""
    from routes.auth import get_session_user
    user = await get_session_user(request)

    if not user:
        return {"favorited": False}

    existing = await db.favorites.find_one({
        "user_id": user["user_id"],
        "recipe_slug": recipe_slug
    })

    return {"favorited": bool(existing)}


@api_router.get("/users/me/favorites")
async def get_my_favorites(request: Request):
    """Get the current user's favorited recipes."""
    from routes.auth import require_auth
    user = await require_auth(request)

    favs = await db.favorites.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "recipe_slug": 1}
    ).sort("created_at", -1).to_list(500)

    if not favs:
        return {"recipes": [], "count": 0}

    slugs = [f["recipe_slug"] for f in favs]

    recipes = await db.recipes.find(
        {"slug": {"$in": slugs}, "status": "published"},
        {"_id": 0}
    ).to_list(500)

    # Preserve favorites order
    recipe_map = {r["slug"]: r for r in recipes}
    ordered = [recipe_map[s] for s in slugs if s in recipe_map]

    return {"recipes": ordered, "count": len(ordered)}

# ============== RATINGS & REVIEWS ROUTES ==============

@api_router.post("/recipes/{recipe_slug}/rate")
async def rate_recipe(recipe_slug: str, rating_create: RatingCreate, current_user: str = Security(get_current_user)):
    """Rate a recipe (1-5 stars)."""
    try:
        # Check if recipe exists
        recipe = await db.recipes.find_one({"slug": recipe_slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if user already rated
        existing = await db.ratings.find_one({"recipe_slug": recipe_slug, "user_email": current_user})
        
        rating_doc = {
            "recipe_slug": recipe_slug,
            "user_email": current_user,
            "rating": rating_create.rating,
            "comment": rating_create.comment,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            # Update existing rating
            await db.ratings.update_one(
                {"recipe_slug": recipe_slug, "user_email": current_user},
                {"$set": rating_doc}
            )
            message = "Rating updated"
        else:
            # Create new rating
            rating_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.ratings.insert_one(rating_doc)
            message = "Rating added"
        
        # Calculate new average
        ratings = await db.ratings.find({"recipe_slug": recipe_slug}).to_list(1000)
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings)
        
        # Update recipe stats
        await db.recipes.update_one(
            {"slug": recipe_slug},
            {
                "$set": {
                    "average_rating": round(avg_rating, 2),
                    "ratings_count": len(ratings)
                }
            }
        )
        
        return {
            "message": message,
            "average_rating": round(avg_rating, 2),
            "ratings_count": len(ratings)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rating error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/recipes/{recipe_slug}/ratings")
async def get_recipe_ratings(recipe_slug: str):
    """Get all ratings for a recipe."""
    ratings = await db.ratings.find(
        {"recipe_slug": recipe_slug},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"ratings": ratings}

@api_router.post("/recipes/{recipe_slug}/comment")
async def add_comment(recipe_slug: str, comment_create: CommentCreate, current_user: str = Security(get_current_user)):
    """Add a comment to a recipe."""
    try:
        # Check if recipe exists
        recipe = await db.recipes.find_one({"slug": recipe_slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        comment_doc = {
            "recipe_slug": recipe_slug,
            "user_email": current_user,
            "comment_text": comment_create.comment_text,
            "parent_comment_id": comment_create.parent_comment_id,
            "upvotes": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.comments.insert_one(comment_doc)
        
        # Update recipe comment count
        comment_count = await db.comments.count_documents({"recipe_slug": recipe_slug, "parent_comment_id": None})
        await db.recipes.update_one(
            {"slug": recipe_slug},
            {"$set": {"comments_count": comment_count}}
        )
        
        return {"message": "Comment added", "comment_count": comment_count}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comment error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/recipes/{recipe_slug}/comments")
async def get_recipe_comments(recipe_slug: str):
    """Get all comments for a recipe."""
    comments = await db.comments.find(
        {"recipe_slug": recipe_slug},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"comments": comments}

@api_router.post("/recipes/{recipe_slug}/verify")
async def verify_recipe(recipe_slug: str, verified: bool, notes: Optional[str] = None, current_user: str = Security(get_current_user)):
    """Mark recipe as verified by user (community verification)."""
    try:
        # Check if recipe exists
        recipe = await db.recipes.find_one({"slug": recipe_slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if user already verified
        existing = await db.verifications.find_one({"recipe_slug": recipe_slug, "user_email": current_user})
        
        verification_doc = {
            "recipe_slug": recipe_slug,
            "user_email": current_user,
            "verified": verified,
            "notes": notes,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            await db.verifications.update_one(
                {"recipe_slug": recipe_slug, "user_email": current_user},
                {"$set": verification_doc}
            )
        else:
            await db.verifications.insert_one(verification_doc)
        
        # Count verifications
        verifications = await db.verifications.count_documents({"recipe_slug": recipe_slug, "verified": True})
        
        # Assign badge
        badge = None
        if verifications >= 50:
            badge = "Highly Authentic"
        elif verifications >= 20:
            badge = "Verified by Community"
        
        # Update recipe
        await db.recipes.update_one(
            {"slug": recipe_slug},
            {
                "$set": {
                    "verifications_count": verifications,
                    "community_badge": badge
                }
            }
        )
        
        return {
            "message": "Verification recorded",
            "verifications_count": verifications,
            "community_badge": badge
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/comments/{comment_id}/upvote")
async def upvote_comment(comment_id: str, current_user: str = Security(get_current_user)):
    """Upvote a comment."""
    result = await db.comments.update_one(
        {"_id": comment_id},
        {"$inc": {"upvotes": 1}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return {"message": "Comment upvoted"}

# ============== TRENDING & DISCOVERY ROUTES ==============

@api_router.get("/recipes/trending")
async def get_trending_recipes(limit: int = 10):
    """Get trending recipes based on recent activity."""
    # Trending = high search_count + recent views + favorites
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("search_count", -1),
        ("favorites_count", -1),
        ("average_rating", -1)
    ]).limit(limit).to_list(limit)
    
    return {"recipes": recipes}

@api_router.get("/recipes/recently-generated")
async def get_recently_generated(limit: int = 10):
    """Get most recently generated recipes."""
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"recipes": recipes}

@api_router.get("/recipes/most-loved")
async def get_most_loved(limit: int = 10, region: Optional[str] = None):
    """Get most loved recipes (by ratings and favorites)."""
    query = {"status": "published"}
    if region:
        query["region"] = region
    
    recipes = await db.recipes.find(
        query,
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("favorites_count", -1)
    ]).limit(limit).to_list(limit)
    
    return {"recipes": recipes}

# ============== CONTINENT ROUTES ==============

@api_router.get("/continents")
async def get_continents():
    """Get all continents with recipe counts."""
    continent_list = ["Europe", "Asia", "Americas", "Africa", "Middle East", "Oceania"]
    
    continents = []
    for continent in continent_list:
        count = await db.recipes.count_documents({"continent": continent, "status": "published"})
        if count > 0:
            continents.append({
                "name": continent,
                "slug": continent.lower().replace(" ", "-"),
                "recipe_count": count
            })
    
    return {"continents": continents}

@api_router.get("/continents/{continent}/countries")
async def get_countries_by_continent(continent: str):
    """Get all countries in a continent that have recipes.
    
    Returns deduplicated, canonical country list with correct recipe counts.
    """
    continent_name = continent.replace("-", " ").title()
    
    # Valid continents for matching
    valid_continents = ["Europe", "Asia", "Americas", "Africa", "Middle East", "Oceania"]
    
    # Handle case variations
    if continent_name not in valid_continents:
        # Try exact match variations
        for vc in valid_continents:
            if vc.lower() == continent_name.lower():
                continent_name = vc
                break
    
    pipeline = [
        {"$match": {
            "continent": continent_name, 
            "status": "published",
            "origin_country": {"$exists": True, "$nin": [None, ""]}
        }},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$sort": {"recipe_count": -1}}
    ]
    
    # Aggregate by canonical country name
    canonical_counts = {}
    async for doc in db.recipes.aggregate(pipeline):
        raw_country = doc["_id"]
        if not raw_country:
            continue
        
        # Normalize to canonical English
        canonical = normalize_country(raw_country)
        
        if canonical in canonical_counts:
            canonical_counts[canonical] += doc["recipe_count"]
        else:
            canonical_counts[canonical] = doc["recipe_count"]
    
    # Build response
    countries = []
    for canonical, count in canonical_counts.items():
        countries.append({
            "name": canonical,
            "slug": canonical.lower().replace(" ", "-"),
            "recipe_count": count
        })
    
    # Sort by recipe count (descending), then name (ascending)
    countries.sort(key=lambda x: (-x["recipe_count"], x["name"]))
    
    return {
        "continent": continent_name,
        "countries": countries,
        "total_recipes": sum(c["recipe_count"] for c in countries)
    }

# ============== SEO ROUTES ==============

@api_router.get("/sitemap.xml")
async def get_sitemap(force_rebuild: bool = False):
    """Generate multilingual sitemap.xml with hreflang annotations for SEO."""
    from fastapi.responses import Response
    import os
    import json
    from datetime import timedelta
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['en', 'es', 'it', 'fr', 'de']
    CACHE_FILE = '/tmp/sitemap_cache.xml'
    CACHE_META = '/tmp/sitemap_cache_meta.json'
    CACHE_TTL_HOURS = 24
    
    base_url = os.environ.get('SITE_URL', 'https://souscheflinguine.com')
    
    # Check cache first
    def is_cache_valid():
        try:
            if os.path.exists(CACHE_META):
                with open(CACHE_META, 'r') as f:
                    meta = json.load(f)
                    generated_at = datetime.fromisoformat(meta.get('generated_at', ''))
                    return datetime.now(timezone.utc) < generated_at + timedelta(hours=CACHE_TTL_HOURS)
        except Exception:
            pass
        return False
    
    if not force_rebuild and is_cache_valid() and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return Response(content=f.read(), media_type="application/xml",
                          headers={"Cache-Control": "public, max-age=3600", "X-Sitemap-Cached": "true"})
    
    # Helper to generate URL entry with hreflang
    def url_entry(path: str, priority: str, changefreq: str, lastmod: str = None):
        entries = ""
        # Generate separate URL entry for each language version
        for lang in SUPPORTED_LANGUAGES:
            lang_path = f"/{lang}{path}" if path != '/' else f"/{lang}"
            entries += "  <url>\n"
            entries += f"    <loc>{base_url}{lang_path}</loc>\n"
            
            if lastmod:
                entries += f"    <lastmod>{lastmod}</lastmod>\n"
            entries += f"    <changefreq>{changefreq}</changefreq>\n"
            entries += f"    <priority>{priority}</priority>\n"
            
            # Add hreflang annotations for ALL language versions
            for alt_lang in SUPPORTED_LANGUAGES:
                alt_path = f"/{alt_lang}{path}" if path != '/' else f"/{alt_lang}"
                entries += f'    <xhtml:link rel="alternate" hreflang="{alt_lang}" href="{base_url}{alt_path}"/>\n'
            
            # x-default points to English
            default_path = f"/en{path}" if path != '/' else "/en"
            entries += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{base_url}{default_path}"/>\n'
            entries += "  </url>\n"
        
        return entries
    
    # Build XML
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    xml_content += '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    
    # Static pages
    # Note: /techniques is now live and indexable
    static_pages = [
        ("/", "1.0", "daily"),
        ("/explore", "0.9", "daily"),
        ("/techniques", "0.7", "weekly"),
        ("/about", "0.6", "monthly"),
        ("/editorial-policy", "0.5", "monthly"),
    ]
    
    for path, priority, changefreq in static_pages:
        xml_content += url_entry(path, priority, changefreq)
    
    # Get continents
    try:
        continents = await db.continents.find({}, {"slug": 1, "_id": 0}).to_list(100)
        for continent in continents:
            slug = continent.get('slug')
            if slug:
                xml_content += url_entry(f"/explore/{slug}", "0.8", "weekly")
                
                # Get countries for this continent
                countries = await db.countries.find({"continent_slug": slug}, {"slug": 1, "_id": 0}).to_list(100)
                for country in countries:
                    country_slug = country.get('slug')
                    if country_slug:
                        xml_content += url_entry(f"/explore/{slug}/{country_slug}", "0.7", "weekly")
    except Exception as e:
        logger.error(f"Error fetching continents: {e}")
        # Fallback to hardcoded continents
        for continent in ["europe", "asia", "americas", "africa", "middle-east", "oceania"]:
            xml_content += url_entry(f"/explore/{continent}", "0.8", "weekly")
    
    # Get all published recipes
    try:
        recipes = await db.recipes.find(
            {"status": "published"},
            {"slug": 1, "date_fetched": 1, "average_rating": 1, "_id": 0}
        ).to_list(10000)
        
        # Sort by rating for priority assignment
        recipes_sorted = sorted(recipes, key=lambda x: x.get('average_rating', 0), reverse=True)
        
        for idx, recipe in enumerate(recipes_sorted):
            slug = recipe.get('slug')
            if not slug:
                continue
            
            # Higher priority for top recipes
            if idx < 10:
                priority = "0.9"
            elif idx < 50:
                priority = "0.8"
            elif idx < 100:
                priority = "0.7"
            else:
                priority = "0.6"
            
            lastmod = recipe.get("date_fetched", "")[:10] if recipe.get("date_fetched") else None
            xml_content += url_entry(f"/recipe/{slug}", priority, "weekly", lastmod)
    except Exception as e:
        logger.error(f"Error fetching recipes: {e}")
    
    xml_content += '</urlset>'
    
    # Cache the result
    try:
        with open(CACHE_FILE, 'w') as f:
            f.write(xml_content)
        with open(CACHE_META, 'w') as f:
            json.dump({'generated_at': datetime.now(timezone.utc).isoformat()}, f)
    except Exception as e:
        logger.warning(f"Failed to cache sitemap: {e}")
    
    return Response(content=xml_content, media_type="application/xml",
                   headers={"Cache-Control": "public, max-age=3600", "X-Sitemap-Cached": "false"})

@api_router.get("/robots.txt")
async def get_robots():
    """Generate robots.txt for SEO."""
    from fastapi.responses import PlainTextResponse
    
    robots_content = """User-agent: *
Allow: /
Allow: /explore
Allow: /recipe/
Disallow: /api/
Disallow: /admin/

Sitemap: https://souschef-linguine.com/api/sitemap.xml
"""
    return PlainTextResponse(content=robots_content)

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {
        "message": "Sous Chef Linguine API",
        "version": "1.0.0",
        "status": "running"
    }

# Serve AI-generated recipe images as static files
from fastapi.staticfiles import StaticFiles
app.mount("/api/recipe-images", StaticFiles(directory="static/recipe-images"), name="recipe-images")

# Include the router in the main app
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(document_router)
app.include_router(translation_router)
app.include_router(sitemap_router, prefix="/api")
app.include_router(search_router)
app.include_router(prerender_router, prefix="/api")
app.include_router(auth_router, prefix="/api")  # Auth routes
app.include_router(techniques_router)  # Techniques routes

# Add CORS middleware
# When credentials=True, we cannot use "*" for origins
# Use the CORS_ORIGINS env variable or fallback to common development/production URLs
cors_origins_str = os.environ.get('CORS_ORIGINS', '')
if cors_origins_str:
    cors_origins = [o.strip() for o in cors_origins_str.split(',') if o.strip()]
else:
    # Default origins for development and production
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://recipe-redesign.preview.emergentagent.com",
        "https://cuisine-babel.emergent.sh"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def create_indexes():
    try:
        # Favorites & reviews unique indexes
        await db.favorites.create_index(
            [("user_id", 1), ("recipe_slug", 1)],
            unique=True,
            background=True
        )
        await db.recipe_reviews.create_index(
            [("user_id", 1), ("recipe_slug", 1)],
            unique=True,
            background=True
        )
        # Recipe search & query indexes
        await db.recipes.create_index(
            [("status", 1), ("slug", 1)],
            background=True
        )
        await db.recipes.create_index(
            [("status", 1), ("recipe_name", 1)],
            background=True
        )
        await db.recipes.create_index(
            [("status", 1), ("origin_country", 1)],
            background=True
        )
        await db.recipes.create_index(
            [("status", 1), ("average_rating", -1), ("ratings_count", -1)],
            background=True
        )
        # Techniques indexes
        await db.techniques.create_index([("slug", 1)], unique=True, background=True)
        await db.techniques.create_index([("status", 1)], background=True)
        await db.techniques.create_index([("category", 1)], background=True)
        logger.info("All MongoDB indexes created/verified.")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()