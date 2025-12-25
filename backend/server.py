from fastapi import FastAPI, APIRouter, HTTPException, Query, Security, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from thefuzz import fuzz, process

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
    lang: Optional[str] = "en",  # Target language (en, it, es, fr, de, etc.)
    auto_generate: bool = True
):
    """Search for recipes with on-demand generation and translation support.
    
    Flow:
    1. First try fuzzy matching to find similar existing recipes
    2. If match found with score >= 75, return that recipe
    3. If target language differs from content language, translate dynamically (NOT saved)
    4. If no match and auto_generate=True:
       - Generate new recipe in ENGLISH (canonical)
       - Save to DB with content_language='en'
       - Translate if needed (NOT saved)
    
    This prevents duplicate recipes for similar queries like:
    - "Carbonara" vs "Pasta Carbonara" → returns same recipe
    
    IMPORTANT: origin_language = the dish's native language (e.g., 'it' for Italian dishes)
               content_language = the language the recipe content is written in (always 'en' for generated recipes)
    """
    from services.sous_chef_ai import sous_chef_ai
    
    try:
        # Normalize language code
        target_lang = lang.lower()[:2] if lang else "en"
        
        # STEP 1: Try fuzzy matching first (this prevents duplicates!)
        similar_recipe = await _find_similar_recipe(db, q, threshold=75)
        
        if similar_recipe:
            logger.info(f"Similar recipe found via fuzzy matching for '{q}': {similar_recipe.get('slug')}")
            
            # Update analytics
            await db.recipe_analytics.update_one(
                {"recipe_slug": similar_recipe["slug"]},
                {
                    "$inc": {"search_count": 1},
                    "$set": {
                        "last_searched_at": datetime.now(timezone.utc).isoformat(),
                        "last_lang_used": target_lang
                    },
                    "$push": {
                        "search_history": {
                            "query": q,
                            "lang": target_lang,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                },
                upsert=True
            )
            
            # Check if translation is needed
            # Use content_language (what the content is actually written in), NOT origin_language
            # Generated recipes are always in English, so content_language defaults to 'en'
            content_lang = similar_recipe.get("content_language", "en")[:2].lower()
            
            if target_lang != content_lang:
                logger.info(f"Translating recipe '{similar_recipe['slug']}' from {content_lang} to {target_lang}")
                try:
                    translated_recipe = await sous_chef_ai.translate_recipe(similar_recipe, target_lang)
                    # Preserve original metadata
                    translated_recipe["slug"] = similar_recipe["slug"]
                    translated_recipe["_translated"] = True
                    translated_recipe["_original_lang"] = content_lang
                    translated_recipe["_display_lang"] = target_lang
                    
                    return {
                        "found": True,
                        "generated": False,
                        "translated": True,
                        "recipe": translated_recipe
                    }
                except Exception as e:
                    logger.warning(f"Translation failed, returning canonical: {str(e)}")
            
            return {
                "found": True,
                "generated": False,
                "translated": False,
                "recipe": similar_recipe
            }
        
        # STEP 2: Try exact regex match as fallback (for edge cases)
        search_query = {
            "$or": [
                {"recipe_name": {"$regex": f"^{re.escape(q)}$", "$options": "i"}},
                {"slug": {"$regex": f"^{re.escape(q.lower().replace(' ', '-'))}$", "$options": "i"}}
            ],
            "status": "published"
        }
        
        recipe = await db.recipes.find_one(search_query, {"_id": 0})
        
        if recipe:
            logger.info(f"Exact recipe found for query '{q}': {recipe['slug']}")
            
            # Update analytics
            await db.recipe_analytics.update_one(
                {"recipe_slug": recipe["slug"]},
                {
                    "$inc": {"search_count": 1},
                    "$set": {
                        "last_searched_at": datetime.now(timezone.utc).isoformat(),
                        "last_lang_used": target_lang
                    },
                    "$push": {
                        "search_history": {
                            "query": q,
                            "lang": target_lang,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    }
                },
                upsert=True
            )
            
            # Check if translation is needed
            # Use content_language (defaults to 'en' for generated recipes)
            content_lang = recipe.get("content_language", "en")[:2].lower()
            
            if target_lang != content_lang:
                logger.info(f"Translating recipe '{recipe['slug']}' from {content_lang} to {target_lang}")
                try:
                    translated_recipe = await sous_chef_ai.translate_recipe(recipe, target_lang)
                    # Preserve original metadata
                    translated_recipe["slug"] = recipe["slug"]
                    translated_recipe["_translated"] = True
                    translated_recipe["_original_lang"] = content_lang
                    translated_recipe["_display_lang"] = target_lang
                    
                    return {
                        "found": True,
                        "generated": False,
                        "translated": True,
                        "recipe": translated_recipe
                    }
                except Exception as e:
                    logger.warning(f"Translation failed, returning canonical: {str(e)}")
            
            return {
                "found": True,
                "generated": False,
                "translated": False,
                "recipe": recipe
            }
        
        # STEP 3: Recipe not found - generate if enabled
        if not auto_generate:
            return {
                "found": False,
                "generated": False,
                "translated": False,
                "message": f"No recipe found for '{q}'"
            }
        
        logger.info(f"Recipe not found for '{q}' - generating on-demand using Sous-Chef Linguine GPT")
        
        # Determine country and region from query (may return None to let AI decide)
        country, region = _infer_country_region(q)
        
        # Generate recipe in ENGLISH (canonical version)
        recipe_data = await recipe_generator.generate_recipe(
            dish_name=q,
            country=country,
            region=region
        )
        
        # Save canonical recipe to database
        await db.recipes.insert_one(recipe_data)
        
        # Remove _id before returning
        recipe_data.pop('_id', None)
        
        # Initialize analytics
        await db.recipe_analytics.insert_one({
            "recipe_slug": recipe_data["slug"],
            "search_count": 1,
            "last_searched_at": datetime.now(timezone.utc).isoformat(),
            "last_lang_used": target_lang,
            "search_history": [{
                "query": q,
                "lang": target_lang,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "generated_on_demand": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Recipe generated and saved for '{q}': {recipe_data['slug']}")
        
        # If requested language is not English, translate the response (but don't save)
        if target_lang != "en":
            logger.info(f"Translating newly generated recipe to {target_lang}")
            try:
                translated_recipe = await sous_chef_ai.translate_recipe(recipe_data, target_lang)
                translated_recipe["slug"] = recipe_data["slug"]
                translated_recipe["_translated"] = True
                translated_recipe["_original_lang"] = "en"
                translated_recipe["_display_lang"] = target_lang
                
                return {
                    "found": False,
                    "generated": True,
                    "translated": True,
                    "recipe": translated_recipe,
                    "message": f"Recipe for '{q}' generated and translated to {target_lang}!"
                }
            except Exception as e:
                logger.warning(f"Translation of new recipe failed: {str(e)}")
        
        return {
            "found": False,
            "generated": True,
            "translated": False,
            "recipe": recipe_data,
            "message": f"Recipe for '{q}' generated successfully by Sous-Chef Linguine!"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error for '{q}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _infer_country_region(dish_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Infer country and region from dish name.
    
    Returns (None, None) if the dish cannot be identified, allowing the AI to determine origin.
    This prevents incorrect country attribution like "Peking Duck" -> Italy.
    """
    dish_lower = dish_name.lower()
    
    # Comprehensive keyword mapping - expanded to cover more cuisines
    cuisine_patterns = {
        # Italian dishes
        ("Italy", "Mediterranean"): [
            'pasta', 'pizza', 'risotto', 'carbonara', 'amatriciana', 'parmigiana', 
            'tiramisu', 'osso', 'gnocchi', 'lasagna', 'lasagne', 'ravioli', 'tortellini',
            'pesto', 'bolognese', 'milanese', 'marinara', 'margherita', 'cacio e pepe',
            'arancini', 'bruschetta', 'focaccia', 'prosciutto', 'ribollita', 'cotoletta',
            'plin', 'polenta', 'saltimbocca', 'carpaccio', 'vitello', 'ossobuco'
        ],
        # Japanese dishes
        ("Japan", "East Asia"): [
            'sushi', 'ramen', 'tempura', 'teriyaki', 'miso', 'udon', 'soba', 'yakitori',
            'tonkatsu', 'tonkotsu', 'gyudon', 'okonomiyaki', 'takoyaki', 'onigiri',
            'bento', 'edamame', 'gyoza', 'matcha', 'sake', 'wasabi', 'dashi', 'nigiri',
            'sashimi', 'maki', 'donburi', 'katsu', 'shabu', 'sukiyaki', 'kaiseki'
        ],
        # Chinese dishes
        ("China", "East Asia"): [
            'peking', 'beijing', 'kung pao', 'kung-pao', 'dim sum', 'wonton', 'chow mein',
            'lo mein', 'fried rice', 'spring roll', 'dumplings', 'mapo tofu', 'char siu',
            'hoisin', 'szechuan', 'sichuan', 'cantonese', 'hakka', 'jiaozi', 'baozi',
            'congee', 'hot pot', 'xiaolongbao', 'xiao long bao', 'dan dan', 'gongbao'
        ],
        # Korean dishes
        ("South Korea", "East Asia"): [
            'kimchi', 'bibimbap', 'bulgogi', 'korean', 'gochujang', 'jjigae', 'samgyeopsal',
            'tteokbokki', 'japchae', 'sundubu', 'galbi', 'kalbi', 'banchan', 'kimbap',
            'gimbap', 'soju', 'makgeolli', 'dakgalbi', 'bossam', 'naengmyeon', '찌개',
            '김치', '불고기', '비빔밥'
        ],
        # Vietnamese dishes
        ("Vietnam", "Southeast Asia"): [
            'pho', 'phở', 'banh mi', 'bánh mì', 'spring roll', 'vietnamese', 'goi cuon',
            'bun', 'bún', 'nuoc mam', 'cao lau', 'com tam', 'che', 'nem'
        ],
        # Thai dishes
        ("Thailand", "Southeast Asia"): [
            'pad thai', 'tom yum', 'green curry', 'red curry', 'thai', 'massaman',
            'satay', 'som tam', 'khao pad', 'panang', 'basil chicken', 'pad krapow',
            'larb', 'mango sticky rice', 'tom kha'
        ],
        # Mexican dishes
        ("Mexico", "Latin America"): [
            'taco', 'burrito', 'enchilada', 'mole', 'pozole', 'tamale', 'quesadilla',
            'guacamole', 'salsa', 'fajita', 'churro', 'ceviche', 'carnitas', 'barbacoa',
            'elote', 'tostada', 'chilaquiles', 'huevos rancheros', 'chiles', 'pastor'
        ],
        # French dishes
        ("France", "Western Europe"): [
            'coq au vin', 'bouillabaisse', 'ratatouille', 'quiche', 'croissant', 
            'cassoulet', 'baguette', 'escargot', 'soufflé', 'souffle', 'crepe',
            'crème brûlée', 'creme brulee', 'foie gras', 'confit', 'bourguignon',
            'béarnaise', 'bearnaise', 'hollandaise', 'béchamel', 'macaron', 'eclair',
            'tarte tatin', 'provençal', 'provencal', 'niçoise', 'nicoise', 'french'
        ],
        # Spanish dishes
        ("Spain", "Mediterranean"): [
            'paella', 'gazpacho', 'spanish tortilla', 'tortilla española', 'tapas',
            'patatas bravas', 'jamon', 'jamón', 'croquetas', 'sangria', 'fabada',
            'pimientos', 'manchego', 'spanish', 'valenciana', 'catalán', 'catalan'
        ],
        # Indian dishes
        ("India", "South Asia"): [
            'curry', 'tikka', 'masala', 'biryani', 'samosa', 'naan', 'roti', 'dosa',
            'paneer', 'dal', 'daal', 'tandoori', 'vindaloo', 'korma', 'butter chicken',
            'chutney', 'pakora', 'paratha', 'idli', 'vada', 'lassi', 'chai'
        ],
        # Greek dishes
        ("Greece", "Mediterranean"): [
            'moussaka', 'souvlaki', 'gyro', 'tzatziki', 'spanakopita', 'greek salad',
            'feta', 'dolma', 'baklava', 'greek', 'horiatiki', 'fasolada'
        ],
        # Middle Eastern dishes
        ("Lebanon", "Middle East"): [
            'hummus', 'falafel', 'tabbouleh', 'baba ganoush', 'shawarma', 'kibbeh',
            'fattoush', 'labneh', 'lebanese', 'levantine'
        ],
        # North African dishes
        ("Morocco", "North Africa"): [
            'tagine', 'couscous', 'moroccan', 'harira', 'bastilla', 'pastilla', 'rfissa'
        ],
        ("Tunisia", "North Africa"): [
            'shakshuka', 'brik', 'lablabi', 'tunisian'
        ],
        # Swedish/Nordic dishes
        ("Sweden", "Nordic"): [
            'köttbullar', 'kottbullar', 'swedish meatball', 'gravlax', 'semla',
            'kanelbulle', 'surströmming', 'janssons frestelse', 'smörgåsbord', 
            'smorgasbord', 'swedish'
        ],
        # German dishes
        ("Germany", "Central Europe"): [
            'schnitzel', 'bratwurst', 'sauerkraut', 'pretzel', 'strudel', 'spätzle',
            'spaetzle', 'currywurst', 'rouladen', 'sauerbraten', 'german'
        ],
        # Hungarian dishes
        ("Hungary", "Central Europe"): [
            'goulash', 'gulyás', 'gulyas', 'paprikash', 'dobos', 'hungarian', 'pörkölt'
        ],
        # British dishes
        ("United Kingdom", "Western Europe"): [
            'fish and chips', 'shepherd\'s pie', 'cottage pie', 'sunday roast',
            'yorkshire pudding', 'bangers and mash', 'full english', 'british',
            'beef wellington', 'wellington', 'cornish pasty', 'trifle', 'scones'
        ],
        # Australian dishes
        ("Australia", "Oceania"): [
            'meat pie', 'lamington', 'vegemite', 'pavlova', 'australian', 'barramundi',
            'anzac biscuit', 'tim tam'
        ]
    }
    
    # Check each cuisine pattern
    for (country, region), keywords in cuisine_patterns.items():
        if any(keyword in dish_lower for keyword in keywords):
            return (country, region)
    
    # IMPORTANT: Return None if we can't identify the cuisine
    # Let the AI determine the correct country of origin
    return (None, None)


async def _find_similar_recipe(db, search_query: str, threshold: int = 75) -> Optional[dict]:
    """Find an existing recipe that matches the search query using fuzzy matching.
    
    This prevents duplicate recipes from being created for similar queries like:
    - "Carbonara" vs "Pasta Carbonara" vs "Spaghetti alla Carbonara"
    - "Beef Wellington" vs "Wellington"
    
    Args:
        db: Database connection
        search_query: The user's search query
        threshold: Minimum fuzzy match score (0-100) to consider a match
        
    Returns:
        Matching recipe dict or None
    """
    # Normalize the search query
    query_normalized = search_query.lower().strip()
    
    # Remove common prefixes/suffixes for better matching
    common_words = ['pasta', 'alla', 'al', 'di', 'con', 'e', 'the', 'with', 'style', 'homemade', 'authentic', 'traditional']
    query_words = query_normalized.split()
    query_core = ' '.join([w for w in query_words if w not in common_words]) or query_normalized
    
    # Get all published recipes for matching
    all_recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0, "recipe_name": 1, "slug": 1}
    ).to_list(1000)
    
    if not all_recipes:
        return None
    
    # Build list of recipe names for fuzzy matching
    recipe_names = []
    recipe_map = {}
    
    for r in all_recipes:
        name = r.get("recipe_name") or ""
        if name:
            recipe_names.append(name)
            recipe_map[name] = r["slug"]
    
    if not recipe_names:
        return None
    
    # Use fuzzy matching to find best match
    # Try full query first
    matches = process.extract(search_query, recipe_names, scorer=fuzz.token_set_ratio, limit=3)
    
    # Also try core query (without common words)
    if query_core != query_normalized:
        core_matches = process.extract(query_core, recipe_names, scorer=fuzz.token_set_ratio, limit=3)
        matches.extend(core_matches)
    
    # Also try partial matching for shorter queries
    partial_matches = process.extract(search_query, recipe_names, scorer=fuzz.partial_ratio, limit=3)
    matches.extend(partial_matches)
    
    # Find the best match above threshold
    best_match = None
    best_score = 0
    
    for match_name, score in matches:
        if score >= threshold and score > best_score:
            best_match = match_name
            best_score = score
    
    if best_match:
        # Get the full recipe
        slug = recipe_map[best_match]
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"}, {"_id": 0})
        if recipe:
            logger.info(f"Fuzzy match found: '{search_query}' -> '{best_match}' (score: {best_score})")
            return recipe
    
    # No match found
    logger.info(f"No fuzzy match found for '{search_query}' (best score: {best_score})")
    return None

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
async def get_featured_recipes(limit: int = 4, lang: str = "en"):
    """Get top featured recipes (excluding the #1 best)."""
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("favorites_count", -1)
    ]).skip(1).limit(limit).to_list(limit)
    
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
    """
    from services.sous_chef_ai import sous_chef_ai
    
    try:
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"}, {"_id": 0})
        
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Normalize language code
        target_lang = lang.lower()[:2] if lang else "en"
        
        # Check if translation is needed
        content_lang = recipe.get("content_language", "en")[:2].lower()
        
        if target_lang != content_lang:
            logger.info(f"Translating recipe '{slug}' from {content_lang} to {target_lang}")
            try:
                translated_recipe = await sous_chef_ai.translate_recipe(recipe, target_lang)
                # Preserve original metadata
                translated_recipe["slug"] = recipe["slug"]
                translated_recipe["_translated"] = True
                translated_recipe["_original_lang"] = content_lang
                translated_recipe["_display_lang"] = target_lang
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

from models.rating import ReviewCreate, Review, ReviewsResponse
from uuid import uuid4

@api_router.post("/recipes/{slug}/review")
async def create_review(slug: str, review: ReviewCreate):
    """Create a new review for a recipe.
    
    No authentication required for MVP.
    Updates the recipe's average_rating and ratings_count.
    """
    try:
        # Verify recipe exists
        recipe = await db.recipes.find_one({"slug": slug, "status": "published"})
        if not recipe:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        # Create review document
        review_doc = {
            "id": str(uuid4()),
            "recipe_slug": slug,
            "rating": review.rating,
            "comment": review.comment.strip() if review.comment else None,
            "language": review.language or "en",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save review to recipe_reviews collection
        await db.recipe_reviews.insert_one(review_doc)
        
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
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        logger.info(f"New review for {slug}: {review.rating} stars (new avg: {new_average:.2f}, count: {new_count})")
        
        # Return the created review (without MongoDB _id)
        review_doc.pop('_id', None)
        
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
async def get_reviews(slug: str, limit: int = 50, offset: int = 0):
    """Get all reviews for a recipe.
    
    Returns reviews sorted by newest first.
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
        
        return {
            "reviews": reviews,
            "total": total,
            "average_rating": recipe.get("average_rating", 0),
            "ratings_count": recipe.get("ratings_count", 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reviews for {slug}: {str(e)}")
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
async def get_countries():
    """Get all countries that have at least one recipe.
    
    Returns a dynamic list based on actual recipe data, not a static list.
    This ensures the Menu Builder shows all available countries.
    """
    # Aggregate distinct countries from recipes collection
    pipeline = [
        {"$match": {"status": "published", "origin_country": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}  # Sort alphabetically by country name
    ]
    
    countries = []
    async for doc in db.recipes.aggregate(pipeline):
        country_name = doc["_id"]
        if country_name:
            countries.append({
                "name": country_name,
                "slug": country_name.lower().replace(" ", "-"),
                "recipe_count": doc["recipe_count"]
            })
    
    # Also check if there are additional countries in the countries collection
    # that might not have recipes yet but should be shown
    static_countries = await db.countries.find({}, {"_id": 0, "name": 1, "slug": 1}).to_list(200)
    existing_names = {c["name"] for c in countries}
    
    for sc in static_countries:
        if sc.get("name") and sc["name"] not in existing_names:
            countries.append({
                "name": sc["name"],
                "slug": sc.get("slug", sc["name"].lower().replace(" ", "-")),
                "recipe_count": 0
            })
    
    # Sort by recipe count (descending), then name (ascending)
    countries.sort(key=lambda x: (-x["recipe_count"], x["name"]))
    
    return {"countries": countries}

@api_router.get("/countries/with-recipes")
async def get_countries_with_recipes(min_recipes: int = 1):
    """Get all countries that have at least min_recipes recipes.
    
    Use this endpoint for Menu Builder to ensure only countries
    with enough recipes for menu generation are shown.
    """
    pipeline = [
        {"$match": {"status": "published", "origin_country": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$match": {"recipe_count": {"$gte": min_recipes}}},
        {"$sort": {"recipe_count": -1, "_id": 1}}
    ]
    
    countries = []
    async for doc in db.recipes.aggregate(pipeline):
        country_name = doc["_id"]
        if country_name:
            countries.append({
                "name": country_name,
                "slug": country_name.lower().replace(" ", "-"),
                "recipe_count": doc["recipe_count"]
            })
    
    return {"countries": countries, "min_recipes": min_recipes}

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
    """Get all countries in a continent that have recipes."""
    continent_name = continent.replace("-", " ").title()
    
    pipeline = [
        {"$match": {"continent": continent_name, "status": "published"}},
        {"$group": {
            "_id": "$origin_country",
            "recipe_count": {"$sum": 1}
        }},
        {"$sort": {"recipe_count": -1}}
    ]
    
    countries = []
    async for doc in db.recipes.aggregate(pipeline):
        if doc["_id"]:
            countries.append({
                "name": doc["_id"],
                "slug": doc["_id"].lower().replace(" ", "-"),
                "recipe_count": doc["recipe_count"]
            })
    
    return {
        "continent": continent_name,
        "countries": countries
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
        except:
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
    static_pages = [
        ("/", "1.0", "daily"),
        ("/explore", "0.9", "daily"),
        ("/about", "0.6", "monthly"),
        ("/editorial-policy", "0.5", "monthly"),
        ("/techniques", "0.7", "weekly"),
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

# Include the router in the main app
app.include_router(api_router)
app.include_router(admin_router)
app.include_router(document_router)
app.include_router(translation_router)
app.include_router(sitemap_router, prefix="/api")
app.include_router(search_router)

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