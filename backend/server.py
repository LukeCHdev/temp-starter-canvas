from fastapi import FastAPI, APIRouter, HTTPException, Query, Security, UploadFile, File
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

@api_router.get("/recipes/search")
async def search_recipes(
    q: str,
    locale: Optional[str] = "en-US",
    auto_generate: bool = True
):
    """Search for recipes with on-demand generation using Sous-Chef Linguine GPT.
    
    If recipe doesn't exist and auto_generate=True, it will be generated automatically.
    """
    try:
        # Search in database first (search both old and new schema fields)
        search_query = {
            "$or": [
                {"recipe_name": {"$regex": q, "$options": "i"}},
                {"title_original": {"$regex": q, "$options": "i"}},
                {"title_translated.en": {"$regex": q, "$options": "i"}},
                {"slug": {"$regex": q.lower().replace(" ", "-"), "$options": "i"}}
            ],
            "status": "published"
        }
        
        recipe = await db.recipes.find_one(search_query, {"_id": 0})
        
        if recipe:
            # Recipe found - update search analytics
            await db.recipe_analytics.update_one(
                {"recipe_slug": recipe["slug"]},
                {
                    "$inc": {"search_count": 1},
                    "$set": {
                        "last_searched_at": datetime.now(timezone.utc).isoformat(),
                        "last_locale_used": locale
                    },
                    "$push": {
                        "search_history": {
                            "query": q,
                            "locale": locale,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                },
                upsert=True
            )
            
            logger.info(f"Recipe found for query '{q}': {recipe['slug']}")
            return {
                "found": True,
                "generated": False,
                "recipe": recipe
            }
        
        # Recipe not found - generate if enabled
        if not auto_generate:
            return {
                "found": False,
                "generated": False,
                "message": f"No recipe found for '{q}'"
            }
        
        logger.info(f"Recipe not found for '{q}' - generating on-demand using Sous-Chef Linguine GPT")
        
        # Determine country and region from query (simplified logic)
        country, region = _infer_country_region(q)
        
        # Generate recipe using Sous-Chef Linguine GPT
        recipe_data = await recipe_generator.generate_recipe(
            dish_name=q,
            country=country,
            region=region
        )
        
        # Save to database (Sous-Chef GPT already enforces authenticity)
        await db.recipes.insert_one(recipe_data)
        
        # Remove _id before returning
        recipe_data.pop('_id', None)
        
        # Initialize analytics
        await db.recipe_analytics.insert_one({
            "recipe_slug": recipe_data["slug"],
            "search_count": 1,
            "last_searched_at": datetime.now(timezone.utc).isoformat(),
            "last_locale_used": locale,
            "search_history": [{
                "query": q,
                "locale": locale,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "generated_on_demand": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Recipe generated and saved for '{q}': {recipe_data['slug']}")
        
        return {
            "found": False,
            "generated": True,
            "recipe": recipe_data,
            "message": f"Recipe for '{q}' generated successfully by Sous-Chef Linguine!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error for '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _infer_country_region(dish_name: str) -> tuple:
    """Infer country and region from dish name.
    
    This is a simplified version. In production, use NLP or a comprehensive mapping.
    """
    dish_lower = dish_name.lower()
    
    # Italian dishes
    if any(word in dish_lower for word in ['pasta', 'pizza', 'risotto', 'carbonara', 'amatriciana', 'parmigiana', 'tiramisu', 'osso']):
        return ("Italy", "Mediterranean")
    
    # Japanese dishes
    if any(word in dish_lower for word in ['sushi', 'ramen', 'tempura', 'teriyaki', 'miso', 'udon', 'soba']):
        return ("Japan", "East Asia")
    
    # Mexican dishes
    if any(word in dish_lower for word in ['taco', 'burrito', 'enchilada', 'mole', 'pozole', 'tamale', 'quesadilla']):
        return ("Mexico", "Latin America")
    
    # French dishes
    if any(word in dish_lower for word in ['coq au vin', 'bouillabaisse', 'ratatouille', 'quiche', 'croissant', 'cassoulet']):
        return ("France", "Mediterranean")
    
    # Swedish dishes
    if any(word in dish_lower for word in ['köttbullar', 'gravlax', 'semla', 'kanelbulle', 'surströmming']):
        return ("Sweden", "Nordic")
    
    # Spanish dishes
    if any(word in dish_lower for word in ['paella', 'gazpacho', 'tortilla', 'tapas', 'churro']):
        return ("Spain", "Mediterranean")
    
    # Default to Italy if unknown
    return ("Italy", "Mediterranean")

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
        query["$or"] = [
            {"recipe_name": {"$regex": search, "$options": "i"}},
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

# ============== HOMEPAGE & EXPLORE ROUTES (must be before /{slug}) ==============

@api_router.get("/recipes/best")
async def get_best_recipe():
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
    
    return {"recipe": recipe}

@api_router.get("/recipes/featured")
async def get_featured_recipes(limit: int = 4):
    """Get top featured recipes (excluding the #1 best)."""
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).skip(1).limit(limit).to_list(limit)
    
    return {"recipes": recipes}

@api_router.get("/recipes/top-worldwide")
async def get_top_worldwide(limit: int = 10):
    """Get top 10 recipes worldwide sorted by rating > reviews > favorites."""
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).limit(limit).to_list(limit)
    
    return {"recipes": recipes}

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
async def get_recipe(slug: str, locale: Optional[str] = "en-US"):
    """Get single recipe by slug."""
    try:
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return recipe
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recipe {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@api_router.post("/recipes/generate")
async def generate_recipe(recipe_create: RecipeCreate):
    """Generate a new recipe using Sous-Chef Linguine GPT."""
    try:
        # Generate recipe
        recipe_data = await recipe_generator.generate_recipe(
            dish_name=recipe_create.dish_name,
            country=recipe_create.country,
            region=recipe_create.region
        )
        
        # Save to database
        await db.recipes.insert_one(recipe_data)
        
        # Remove _id before returning
        recipe_data.pop('_id', None)
        
        return {
            "message": "Recipe generated successfully by Sous-Chef Linguine",
            "recipe": recipe_data
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
async def scale_recipe(
    recipe_slug: str,
    target_servings: int,
    food_type: Optional[str] = "meat",
    cooking_method: Optional[str] = None
):
    """Scale a recipe to target servings with adaptive cooking time calculation."""
    try:
        recipe = await db.recipes.find_one({"slug": recipe_slug}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Import adaptive cooking engine
        from services.adaptive_cooking import adaptive_cooking_engine
        
        # Basic scaling (quantities)
        scaled_recipe = scaling_engine.scale_recipe(recipe, target_servings)
        
        # Calculate adaptive cooking times
        base_servings = recipe.get('scaling_info', {}).get('base_servings', 4)
        
        # Assume average serving weight (this could be more sophisticated)
        base_weight = base_servings * 0.25  # 250g per serving
        target_weight = target_servings * 0.25
        
        # Add adaptive cooking notes
        adaptive_notes = []
        for level in scaled_recipe.get('authenticity_levels', []):
            for step in level.get('method', []):
                if step.get('timing'):
                    # Extract base time (simplified)
                    import re
                    time_match = re.search(r'(\d+)', step['timing'])
                    if time_match:
                        base_time = int(time_match.group(1))
                        
                        adaptive_result = adaptive_cooking_engine.calculate_cooking_time(
                            food_type=food_type,
                            base_weight=base_weight,
                            target_weight=target_weight,
                            base_time=base_time,
                            cooking_method=cooking_method
                        )
                        
                        adaptive_notes.append({
                            'step': step['step_number'],
                            'original_time': base_time,
                            'adapted_time': adaptive_result['adapted_time_minutes'],
                            'notes': adaptive_result['notes'],
                            'temperature_note': adaptive_result['temperature_note']
                        })
        
        scaled_recipe['adaptive_cooking_notes'] = adaptive_notes
        
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

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {
        "message": "Sous Chef Linguine API",
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