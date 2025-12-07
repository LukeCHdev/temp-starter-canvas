from fastapi import FastAPI, APIRouter, HTTPException, Query, Security
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

# Import models
from models.recipe import Recipe, RecipeCreate, RecipeReject
from models.region import Region, RegionCreate
from models.country import Country, CountryCreate
from models.user import User, UserCreate, UserLogin, Token, SavedRecipe

# Import services
from services.recipe_generator import recipe_generator
from services.authenticity_engine import authenticity_engine
from services.menu_builder_service import menu_builder_service
from services.scaling_engine import scaling_engine
from services.substitution_engine import substitution_engine
from services.translation_engine import translation_engine
from services.locale_service import locale_service

# Import auth utilities
from utils.auth import hash_password, verify_password, create_access_token, get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
        query["region"] = region
    if country:
        query["country"] = country
    if search:
        query["$or"] = [
            {"title_original": {"$regex": search, "$options": "i"}},
            {"title_translated.en": {"$regex": search, "$options": "i"}}
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

@api_router.get("/recipes/{slug}")
async def get_recipe(slug: str):
    """Get single recipe by slug."""
    recipe = await db.recipes.find_one({"slug": slug, "status": "published"}, {"_id": 0})
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return recipe

@api_router.post("/recipes/generate")
async def generate_recipe(recipe_create: RecipeCreate):
    """Generate a new recipe using AI."""
    try:
        # Generate recipe
        recipe_data = await recipe_generator.generate_recipe(
            dish_name=recipe_create.dish_name,
            country=recipe_create.country,
            region=recipe_create.region
        )
        
        # Validate authenticity
        is_valid, rejection_reason, validation_report = authenticity_engine.validate_recipe(recipe_data)
        
        if not is_valid:
            # Mark as rejected
            recipe_data['status'] = 'rejected'
            recipe_data['rejection_reason'] = rejection_reason
            await db.recipes.insert_one(recipe_data)
            
            raise HTTPException(
                status_code=400,
                detail=f"Recipe rejected: {rejection_reason}",
                headers={"X-Validation-Report": str(validation_report)}
            )
        
        # Save to database
        await db.recipes.insert_one(recipe_data)
        
        return {
            "message": "Recipe generated successfully",
            "recipe": recipe_data,
            "validation_report": validation_report
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
async def get_countries():
    """Get all countries."""
    countries = await db.countries.find({}, {"_id": 0}).to_list(200)
    return {"countries": countries}

@api_router.get("/countries/{slug}")
async def get_country(slug: str):
    """Get single country by slug."""
    country = await db.countries.find_one({"slug": slug}, {"_id": 0})
    
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return country

# ============== MENU BUILDER ROUTES ==============

@api_router.post("/menu-builder")
async def build_menu(region: str):
    """Generate a culturally coherent menu."""
    try:
        # Get available recipes from region
        recipes = await db.recipes.find(
            {"region": region, "status": "published"},
            {"_id": 0}
        ).to_list(50)
        
        if len(recipes) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough recipes for {region}. Need at least 3."
            )
        
        # Generate menu
        menu = await menu_builder_service.generate_menu(region, recipes)
        
        # Cache menu
        menu['generated_at'] = datetime.now(timezone.utc).isoformat()
        await db.menus.insert_one(menu)
        
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
async def scale_recipe(recipe_slug: str, target_servings: int):
    """Scale a recipe to target servings."""
    try:
        recipe = await db.recipes.find_one({"slug": recipe_slug}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        scaled_recipe = scaling_engine.scale_recipe(recipe, target_servings)
        
        return scaled_recipe
    
    except Exception as e:
        logger.error(f"Scaling error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== LOCALE ROUTES ==============

@api_router.post("/locale/detect")
async def detect_locale(browser_locale: Optional[str] = None, geo_location: Optional[str] = None):
    """Detect user locale and return settings."""
    locale_settings = locale_service.detect_locale(browser_locale, geo_location)
    return locale_settings

# ============== AUTHENTICATION ROUTES ==============

@api_router.post("/auth/register", response_model=Token)
async def register(user_create: UserCreate):
    """Register a new user."""
    try:
        # Check if user exists
        existing_user = await db.users.find_one({"email": user_create.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = hash_password(user_create.password)
        
        # Create user document
        user_doc = {
            "email": user_create.email,
            "password_hash": hashed_password,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(user_doc)
        
        # Create access token
        access_token = create_access_token(data={"sub": user_create.email})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Login user."""
    try:
        # Find user
        user = await db.users.find_one({"email": user_login.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(user_login.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token(data={"sub": user_login.email})
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: str = Security(get_current_user)):
    """Get current user info."""
    user = await db.users.find_one({"email": current_user}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ============== FAVORITES ROUTES ==============

@api_router.post("/favorites/{recipe_slug}")
async def save_recipe(recipe_slug: str, current_user: str = Security(get_current_user)):
    """Save a recipe to favorites."""
    try:
        # Check if recipe exists
        recipe = await db.recipes.find_one({"slug": recipe_slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Check if already saved
        existing = await db.saved_recipes.find_one({
            "user_email": current_user,
            "recipe_slug": recipe_slug
        })
        
        if existing:
            return {"message": "Recipe already in favorites"}
        
        # Save recipe
        saved_doc = {
            "user_email": current_user,
            "recipe_slug": recipe_slug,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.saved_recipes.insert_one(saved_doc)
        
        return {"message": "Recipe saved to favorites"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save recipe error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/favorites/{recipe_slug}")
async def unsave_recipe(recipe_slug: str, current_user: str = Security(get_current_user)):
    """Remove a recipe from favorites."""
    try:
        result = await db.saved_recipes.delete_one({
            "user_email": current_user,
            "recipe_slug": recipe_slug
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Recipe not in favorites")
        
        return {"message": "Recipe removed from favorites"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unsave recipe error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/favorites")
async def get_favorites(current_user: str = Security(get_current_user)):
    """Get user's saved recipes."""
    try:
        # Get saved recipe slugs
        saved = await db.saved_recipes.find(
            {"user_email": current_user},
            {"_id": 0, "recipe_slug": 1}
        ).to_list(1000)
        
        if not saved:
            return {"recipes": []}
        
        slugs = [s["recipe_slug"] for s in saved]
        
        # Get full recipe details
        recipes = await db.recipes.find(
            {"slug": {"$in": slugs}, "status": "published"},
            {"_id": 0}
        ).to_list(1000)
        
        return {"recipes": recipes}
    
    except Exception as e:
        logger.error(f"Get favorites error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {
        "message": "Sous Chef Linguini API",
        "version": "1.0.0",
        "status": "running"
    }

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()