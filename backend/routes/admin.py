# Admin Routes for Recipe Management

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import json
import logging
import httpx
import re
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from rapidfuzz import fuzz

# Import canonical schema validation
from models.recipe import validate_canonical_recipe, normalize_to_canonical

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME')]

# Admin password from environment
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# ============== MODELS ==============

class AdminLogin(BaseModel):
    password: str

class RecipeJSON(BaseModel):
    recipe_json: Dict[str, Any]
    validate_schema: bool = True  # Enable schema validation by default

class ScrapeRequest(BaseModel):
    url: str

class RecipeUpdate(BaseModel):
    recipe_data: Dict[str, Any]

class RecipeStatusUpdate(BaseModel):
    status: Optional[str] = None
    archived: Optional[bool] = None

class BulkPublishResponse(BaseModel):
    success: bool
    published_count: int
    blocked_count: int
    published_slugs: List[str]
    blocked_slugs: List[str]
    dry_run: bool

# ============== AUTH HELPERS ==============

def verify_admin_token(authorization: str = Header(None)) -> bool:
    """Verify the admin token from header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Format: "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = parts[1]
    
    # Simple token validation - in production use JWT
    # Token is base64 of password for simplicity
    import base64
    try:
        decoded = base64.b64decode(token).decode('utf-8')
        if decoded != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

# ============== AUTH ROUTES ==============

@admin_router.post("/login")
async def admin_login(login: AdminLogin):
    """Admin login - returns a token if password is correct."""
    if login.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Generate simple token (base64 encoded password)
    import base64
    token = base64.b64encode(ADMIN_PASSWORD.encode()).decode('utf-8')
    
    return {
        "success": True,
        "token": token,
        "message": "Login successful"
    }

@admin_router.get("/verify")
async def verify_admin(authorized: bool = Depends(verify_admin_token)):
    """Verify if the current token is valid."""
    return {"valid": True}

# ============== RECIPE MANAGEMENT ROUTES ==============

@admin_router.get("/recipes")
async def get_all_recipes(
    authorized: bool = Depends(verify_admin_token),
    status_filter: Optional[str] = None
):
    """Get all recipes for admin management with optional status filter.
    
    Query params:
    - status_filter: 'published', 'unpublished', 'draft', or 'all' (default: 'all')
    """
    query = {}
    
    if status_filter and status_filter != 'all':
        query["status"] = status_filter
    
    recipes = await db.recipes.find(
        query,
        {"_id": 0}
    ).sort("date_fetched", -1).to_list(1000)
    
    # Get counts for UI
    total_all = await db.recipes.count_documents({})
    total_published = await db.recipes.count_documents({"status": "published"})
    total_unpublished = await db.recipes.count_documents({"status": "unpublished"})
    total_draft = await db.recipes.count_documents({"status": "draft"})
    
    return {
        "recipes": recipes,
        "total": len(recipes),
        "counts": {
            "all": total_all,
            "published": total_published,
            "unpublished": total_unpublished,
            "draft": total_draft
        },
        "current_filter": status_filter or "all"
    }

@admin_router.get("/recipes/{slug}")
async def get_recipe_for_edit(slug: str, authorized: bool = Depends(verify_admin_token)):
    """Get a single recipe for editing."""
    recipe = await db.recipes.find_one({"slug": slug}, {"_id": 0})
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {"recipe": recipe}

@admin_router.put("/recipes/{slug}")
async def update_recipe(slug: str, update: RecipeUpdate, authorized: bool = Depends(verify_admin_token)):
    """Update an existing recipe."""
    try:
        recipe_data = update.recipe_data
        
        # Add updated timestamp
        recipe_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update the recipe
        result = await db.recipes.update_one(
            {"slug": slug},
            {"$set": recipe_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Recipe not found")
        
        return {
            "success": True,
            "slug": recipe_data.get("slug", slug),
            "message": "Recipe updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.delete("/recipes/{slug}")
async def delete_recipe(slug: str, authorized: bool = Depends(verify_admin_token)):
    """Delete a recipe."""
    result = await db.recipes.delete_one({"slug": slug})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {
        "success": True,
        "message": f"Recipe '{slug}' deleted successfully"
    }

# ============== IMPORT ROUTES ==============

def generate_slug(recipe_name: str, country: str = "") -> str:
    """Generate a URL-friendly slug from recipe name and country."""
    import re
    import unicodedata
    
    text = f"{recipe_name} {country}".strip()
    # Normalize Unicode
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    # Convert to lowercase and replace spaces
    slug = text.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-') or 'recipe'

def get_continent(country: str) -> str:
    """Get continent for a country."""
    COUNTRY_TO_CONTINENT = {
        # Europe
        "Italy": "Europe", "France": "Europe", "Spain": "Europe", "Germany": "Europe",
        "United Kingdom": "Europe", "Greece": "Europe", "Portugal": "Europe", "Sweden": "Europe",
        "Norway": "Europe", "Denmark": "Europe", "Finland": "Europe", "Netherlands": "Europe",
        "Belgium": "Europe", "Austria": "Europe", "Switzerland": "Europe", "Poland": "Europe",
        "Czech Republic": "Europe", "Hungary": "Europe", "Romania": "Europe", "Bulgaria": "Europe",
        "Croatia": "Europe", "Serbia": "Europe", "Ireland": "Europe", "Russia": "Europe",
        "Ukraine": "Europe", "Turkey": "Europe", "Albania": "Europe", "Bosnia and Herzegovina": "Europe",
        "Montenegro": "Europe", "North Macedonia": "Europe", "Slovenia": "Europe", "Slovakia": "Europe",
        "Moldova": "Europe", "Belarus": "Europe", "Lithuania": "Europe", "Latvia": "Europe",
        "Estonia": "Europe", "Iceland": "Europe", "Luxembourg": "Europe", "Malta": "Europe",
        "Cyprus": "Europe",
        # Asia
        "Japan": "Asia", "China": "Asia", "South Korea": "Asia", "North Korea": "Asia",
        "Vietnam": "Asia", "Thailand": "Asia", "Indonesia": "Asia", "Malaysia": "Asia",
        "Singapore": "Asia", "Philippines": "Asia", "India": "Asia", "Pakistan": "Asia",
        "Bangladesh": "Asia", "Sri Lanka": "Asia", "Nepal": "Asia", "Myanmar": "Asia",
        "Cambodia": "Asia", "Laos": "Asia", "Taiwan": "Asia", "Hong Kong": "Asia",
        "Mongolia": "Asia", "Kazakhstan": "Asia",
        # Americas
        "United States": "Americas", "USA": "Americas", "Mexico": "Americas", "Canada": "Americas",
        "Brazil": "Americas", "Argentina": "Americas", "Peru": "Americas", "Colombia": "Americas",
        "Chile": "Americas", "Venezuela": "Americas", "Ecuador": "Americas", "Cuba": "Americas",
        "Jamaica": "Americas", "Dominican Republic": "Americas", "Puerto Rico": "Americas",
        "Guatemala": "Americas", "Honduras": "Americas", "Costa Rica": "Americas", "Panama": "Americas",
        # Africa
        "Morocco": "Africa", "Egypt": "Africa", "Ethiopia": "Africa", "Nigeria": "Africa",
        "South Africa": "Africa", "Kenya": "Africa", "Ghana": "Africa", "Senegal": "Africa",
        "Tunisia": "Africa", "Algeria": "Africa", "Tanzania": "Africa",
        # Middle East
        "Lebanon": "Middle East", "Israel": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
        "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East", "UAE": "Middle East",
        "Jordan": "Middle East", "Syria": "Middle East", "Yemen": "Middle East", "Oman": "Middle East",
        "Kuwait": "Middle East", "Bahrain": "Middle East", "Qatar": "Middle East", "Palestine": "Middle East",
        "Georgia": "Middle East", "Armenia": "Middle East", "Azerbaijan": "Middle East",
        # Oceania
        "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania", "Papua New Guinea": "Oceania",
    }
    return COUNTRY_TO_CONTINENT.get(country, "Unknown")

@admin_router.post("/import/json")
async def import_json(recipe: RecipeJSON, authorized: bool = Depends(verify_admin_token)):
    """Import a recipe from JSON using the CANONICAL SCHEMA.
    
    All imported recipes are validated and normalized to ensure
    consistency across the platform.
    """
    try:
        recipe_data = recipe.recipe_json
        
        # Step 1: Validate against canonical schema
        if recipe.validate_schema:
            is_valid, errors = validate_canonical_recipe(recipe_data)
            if not is_valid:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Schema validation failed: {'; '.join(errors)}"
                )
        
        # Step 2: Normalize to canonical format
        normalized_data = normalize_to_canonical(recipe_data)
        
        # Validate required fields after normalization
        recipe_name = normalized_data.get('recipe_name', '')
        if not recipe_name:
            raise HTTPException(status_code=400, detail="recipe_name is required")
        
        # Step 3: Generate slug and check for duplicates
        origin_country = normalized_data.get('origin_country', '')
        slug = recipe_data.get('slug') or generate_slug(recipe_name, origin_country)
        
        existing = await db.recipes.find_one({"slug": slug})
        if existing:
            raise HTTPException(status_code=400, detail=f"Recipe with slug '{slug}' already exists")
        
        # Step 4: Enrich with system metadata
        enriched_recipe = {
            **normalized_data,
            "slug": slug,
            "continent": normalized_data.get('continent') or get_continent(origin_country),
            "content_language": normalized_data.get('content_language', 'en'),
            "status": normalized_data.get('status', 'published'),
            "date_fetched": datetime.now(timezone.utc).isoformat(),
            "gpt_used": normalized_data.get('gpt_used', 'Manual Import'),
            "collection_method": normalized_data.get('collection_method', 'admin_import'),
            # Initialize analytics
            "views_count": normalized_data.get('views_count', 0),
            "favorites_count": normalized_data.get('favorites_count', 0),
            "average_rating": normalized_data.get('average_rating', 0),
            "ratings_count": normalized_data.get('ratings_count', 0),
            "comments_count": normalized_data.get('comments_count', 0),
        }
        
        # Step 5: Save to database
        await db.recipes.insert_one(enriched_recipe)
        
        logger.info(f"Recipe imported via admin: {slug}")
        
        return {
            "success": True,
            "slug": slug,
            "message": f"Recipe '{recipe_name}' imported successfully (canonical schema)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), authorized: bool = Depends(verify_admin_token)):
    """Import recipes from CSV file."""
    try:
        import csv
        from io import StringIO
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Parse CSV
        reader = csv.DictReader(StringIO(csv_content))
        
        imported = 0
        skipped = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            try:
                recipe_name = row.get('recipe_name', '').strip()
                if not recipe_name:
                    errors.append(f"Row {row_num}: Missing recipe_name")
                    skipped += 1
                    continue
                
                origin_country = row.get('origin_country', '').strip()
                slug = row.get('slug') or generate_slug(recipe_name, origin_country)
                
                # Check for duplicates
                existing = await db.recipes.find_one({"slug": slug})
                if existing:
                    skipped += 1
                    continue
                
                # Parse complex fields
                no_no_rules = [r.strip() for r in row.get('no_no_rules', '').split(';') if r.strip()]
                special_techniques = [t.strip() for t in row.get('special_techniques', '').split(';') if t.strip()]
                instructions = [i.strip() for i in row.get('instructions', '').split(';') if i.strip()]
                
                # Parse ingredients
                ingredients = []
                ingredients_str = row.get('ingredients', '')
                if ingredients_str:
                    for ing in ingredients_str.split(';'):
                        parts = ing.split(':')
                        if len(parts) >= 3:
                            ingredients.append({
                                "item": parts[0].strip(),
                                "amount": parts[1].strip(),
                                "unit": parts[2].strip(),
                                "notes": parts[3].strip() if len(parts) > 3 else ""
                            })
                
                # Parse wine pairings
                wine_pairing = {"recommended_wines": [], "notes": row.get('wine_notes', '')}
                for i in range(1, 4):
                    wine_name = row.get(f'wine_name_{i}', '').strip()
                    if wine_name:
                        wine_pairing["recommended_wines"].append({
                            "name": wine_name,
                            "region": row.get(f'wine_region_{i}', '').strip(),
                            "reason": row.get(f'wine_reason_{i}', '').strip()
                        })
                
                # Build recipe document
                recipe = {
                    "recipe_name": recipe_name,
                    "slug": slug,
                    "origin_country": origin_country,
                    "origin_region": row.get('origin_region', '').strip(),
                    "origin_language": row.get('origin_language', 'en').strip(),
                    "continent": get_continent(origin_country),
                    "authenticity_level": int(row.get('authenticity_level', 3)),
                    "history_summary": row.get('history_summary', '').strip(),
                    "characteristic_profile": row.get('characteristic_profile', '').strip(),
                    "no_no_rules": no_no_rules,
                    "special_techniques": special_techniques,
                    "technique_links": [],
                    "ingredients": ingredients,
                    "instructions": instructions,
                    "photos": [{"image_url": row.get('photo_url', ''), "credit": row.get('photo_credit', '')}] if row.get('photo_url') else [],
                    "youtube_links": [{"url": row.get('youtube_url', ''), "title": row.get('youtube_title', '')}] if row.get('youtube_url') else [],
                    "original_source_urls": [{"url": row.get('source_url', ''), "type": row.get('source_type', 'traditional'), "language": row.get('source_language', '')}] if row.get('source_url') else [],
                    "wine_pairing": wine_pairing,
                    "status": "published",
                    "date_fetched": datetime.now(timezone.utc).isoformat(),
                    "gpt_used": "CSV Import",
                    "collection_method": "csv_import",
                    "views_count": 0,
                    "favorites_count": 0,
                    "average_rating": 0,
                    "ratings_count": 0,
                    "comments_count": 0,
                }
                
                await db.recipes.insert_one(recipe)
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                skipped += 1
        
        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "errors": errors[:20]  # Limit errors returned
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/import/scrape")
async def scrape_and_import(request: ScrapeRequest, authorized: bool = Depends(verify_admin_token)):
    """Scrape a URL and generate a recipe using Sous-Chef AI."""
    try:
        url = request.url
        
        # Scrape the URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            html_content = response.text
        
        # Extract text from HTML (simple extraction)
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside'}
                self.current_tag = None
                
            def handle_starttag(self, tag, attrs):
                self.current_tag = tag
                
            def handle_endtag(self, tag):
                self.current_tag = None
                
            def handle_data(self, data):
                if self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text_parts.append(text)
        
        extractor = TextExtractor()
        extractor.feed(html_content)
        extracted_text = ' '.join(extractor.text_parts)
        
        # Limit text length for AI processing
        extracted_text = extracted_text[:8000]
        
        # Send to Sous-Chef AI for normalization
        from services.sous_chef_ai import sous_chef_ai
        
        # Create a special prompt for scraping
        scrape_prompt = f"""Based on the following extracted text from a recipe page, generate a properly structured recipe JSON.
Extracted text:
{extracted_text}

Source URL: {url}

Generate the recipe in standard JSON format."""
        
        # Generate using AI
        recipe_json = await sous_chef_ai.generate_recipe(scrape_prompt[:4000])
        
        # Add source URL
        if recipe_json:
            recipe_json['original_source_urls'] = [{
                'url': url,
                'type': 'scraped',
                'language': 'unknown'
            }]
        
        return {
            "success": True,
            "recipe_json": recipe_json,
            "source_url": url,
            "message": "Recipe extracted. Review and save."
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/csv-template")
async def get_csv_template(authorized: bool = Depends(verify_admin_token)):
    """Get the CSV template headers and example."""
    return {
        "headers": [
            "recipe_name", "origin_country", "origin_region", "origin_language",
            "authenticity_level", "history_summary", "characteristic_profile",
            "no_no_rules", "special_techniques", "ingredients", "instructions",
            "wine_name_1", "wine_region_1", "wine_reason_1",
            "wine_name_2", "wine_region_2", "wine_reason_2",
            "wine_notes", "photo_url", "photo_credit",
            "youtube_url", "youtube_title", "source_url", "source_type", "source_language"
        ],
        "notes": {
            "no_no_rules": "Semicolon-separated list",
            "special_techniques": "Semicolon-separated list",
            "ingredients": "Format: item:amount:unit:notes separated by semicolons",
            "instructions": "Semicolon-separated steps",
            "authenticity_level": "1 (highest) to 5 (lowest)"
        }
    }

@admin_router.get("/canonical-schema")
async def get_canonical_schema(authorized: bool = Depends(verify_admin_token)):
    """Get the canonical recipe schema definition.
    
    This is the SINGLE SOURCE OF TRUTH for all recipe data.
    Use this when creating recipes in ChatGPT or other external tools.
    """
    return {
        "schema_version": "1.0",
        "description": "Canonical Recipe Schema for Sous Chef Linguine",
        "example": {
            "recipe_name": "Spaghetti alla Carbonara",
            "origin_country": "Italy",
            "origin_region": "Lazio",
            "origin_language": "it",
            "authenticity_level": 1,
            "history_summary": "A Roman pasta dish documented by traditional institutions...",
            "characteristic_profile": "Rich, salty, creamy texture with smoky guanciale and pecorino romano.",
            "no_no_rules": [
                "Never use cream",
                "Never use garlic or onion",
                "Must use guanciale, not pancetta or bacon"
            ],
            "special_techniques": [
                "mantecatura (creaming with pasta water)",
                "tempering eggs off heat"
            ],
            "technique_links": [
                {
                    "technique": "mantecatura",
                    "url": "https://youtube.com/example",
                    "description": "How to cream pasta properly"
                }
            ],
            "ingredients": [
                {"item": "Spaghetti", "amount": "380", "unit": "g", "notes": ""},
                {"item": "Guanciale", "amount": "150", "unit": "g", "notes": "cut into strips"}
            ],
            "instructions": [
                "Cook the guanciale in a cold pan until crispy",
                "Mix egg yolks with pecorino and black pepper",
                "Cook pasta al dente, reserve pasta water",
                "Combine off heat using mantecatura technique"
            ],
            "wine_pairing": {
                "recommended_wines": [
                    {
                        "name": "Frascati Superiore DOCG",
                        "region": "Lazio",
                        "reason": "High acidity cuts through richness"
                    }
                ],
                "notes": "Central Italian whites work best"
            }
        },
        "required_fields": [
            "recipe_name"
        ],
        "field_definitions": {
            "recipe_name": "Name of the dish in its original language",
            "origin_country": "Country of origin",
            "origin_region": "Specific region within the country",
            "origin_language": "2-letter language code (it, fr, ja, etc.)",
            "authenticity_level": "1=Official/DOP, 2=Traditional, 3=Regional, 4=Recognized, 5=Modern",
            "history_summary": "Brief history of the dish",
            "characteristic_profile": "Taste and texture description",
            "no_no_rules": "Array of strings - what NOT to do when making this dish",
            "special_techniques": "Array of strings - traditional cooking techniques",
            "technique_links": "Array of {technique, url, description} - links to tutorials",
            "ingredients": "Array of {item, amount, unit, notes}",
            "instructions": "Array of strings - step-by-step cooking instructions",
            "wine_pairing": "{recommended_wines: [{name, region, reason}], notes}"
        },
        "notes": {
            "technique_links": "REQUIRED when special_techniques exist - link to tutorials",
            "translations": "Computed on demand, NOT saved as new recipes",
            "authenticity_level": "Lower number = more authentic (1 is highest)"
        }
    }

# ============== STATS ROUTES ==============

@admin_router.get("/stats")
async def get_admin_stats(authorized: bool = Depends(verify_admin_token)):
    """Get admin dashboard statistics with detailed breakdown."""
    # Total counts
    total_recipes = await db.recipes.count_documents({})
    
    # Status breakdown (the field public site filters on)
    published_count = await db.recipes.count_documents({"status": "published"})
    unpublished_count = await db.recipes.count_documents({"status": "unpublished"})
    draft_count = await db.recipes.count_documents({"status": "draft"})
    no_status = await db.recipes.count_documents({
        "$or": [
            {"status": {"$exists": False}},
            {"status": None}
        ]
    })
    other_status = total_recipes - published_count - unpublished_count - draft_count - no_status
    
    # Visibility issues for published recipes
    missing_continent = await db.recipes.count_documents({
        "status": "published",
        "$or": [{"continent": {"$exists": False}}, {"continent": None}, {"continent": ""}]
    })
    missing_country = await db.recipes.count_documents({
        "status": "published",
        "$or": [{"origin_country": {"$exists": False}}, {"origin_country": None}, {"origin_country": ""}]
    })
    missing_required = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"recipe_name": {"$exists": False}}, {"recipe_name": None}, {"recipe_name": ""},
            {"ingredients": {"$exists": False}}, {"ingredients": None}, {"ingredients": {"$size": 0}},
            {"instructions": {"$exists": False}}, {"instructions": None}, {"instructions": {"$size": 0}}
        ]
    })
    
    # Truly visible on public site
    truly_visible = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$exists": True, "$ne": None, "$ne": ""},
        "origin_country": {"$exists": True, "$ne": None, "$ne": ""},
        "recipe_name": {"$exists": True, "$ne": None, "$ne": ""}
    })
    
    # Test/placeholder detection
    test_placeholder_count = await db.recipes.count_documents({
        "$or": [
            {"recipe_name": {"$regex": "test", "$options": "i"}},
            {"recipe_name": {"$regex": "placeholder", "$options": "i"}},
            {"recipe_name": {"$regex": "sample", "$options": "i"}},
            {"recipe_name": {"$regex": "example", "$options": "i"}}
        ]
    })
    
    # Recipes by country
    countries_pipeline = [
        {"$group": {"_id": "$origin_country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    countries = await db.recipes.aggregate(countries_pipeline).to_list(10)
    
    # Recipes by continent
    continents_pipeline = [
        {"$group": {"_id": "$continent", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    continents = await db.recipes.aggregate(continents_pipeline).to_list(10)
    
    # Recent recipes
    recent = await db.recipes.find(
        {},
        {"_id": 0, "recipe_name": 1, "slug": 1, "date_fetched": 1, "status": 1}
    ).sort("date_fetched", -1).limit(5).to_list(5)
    
    # Database info
    db_info = {
        "database": os.environ.get('DB_NAME', 'unknown'),
        "collection": "recipes",
        "mongo_url": os.environ.get('MONGO_URL', 'unknown')[:30] + "..."
    }
    
    return {
        "total_recipes": total_recipes,
        "status_breakdown": {
            "published": published_count,
            "unpublished": unpublished_count,
            "draft": draft_count,
            "no_status": no_status,
            "other": other_status
        },
        "visibility": {
            "truly_visible": truly_visible,
            "missing_continent": missing_continent,
            "missing_country": missing_country,
            "missing_required_fields": missing_required,
            "gap": published_count - truly_visible
        },
        "test_placeholder_count": test_placeholder_count,
        "public_site_shows": truly_visible,
        "recipes_by_country": [{"country": c["_id"], "count": c["count"]} for c in countries if c["_id"]],
        "recipes_by_continent": [{"continent": c["_id"], "count": c["count"]} for c in continents if c["_id"]],
        "recent_recipes": recent,
        "db_info": db_info,
        "filter_explanation": "Public site filters by status='published' + required fields (continent, country, name)."
    }


# ============== REVIEW QUEUE ROUTES ==============

# Placeholder/test patterns to detect unsafe recipes
PLACEHOLDER_PATTERNS = [
    r'\btest\b', r'\bplaceholder\b', r'\bsample\b', r'\bexample\b', r'\bdemo\b',
    r'\btodo\b', r'\bfixme\b', r'\bxxx\b', r'\btemp\b'
]

# Countries that often indicate placeholder data
SUSPICIOUS_COUNTRIES = ['south-korea', 'russia', 'latvia', 'test', 'placeholder', 'unknown', '']


def detect_flags(recipe: dict, all_recipes: List[dict] = None) -> dict:
    """
    Detect issues with a recipe and return flags.
    Returns: {flags: [], duplicate_of: str|None, is_safe_to_publish: bool}
    """
    flags = []
    duplicate_of = None
    
    recipe_name = recipe.get('recipe_name', '') or ''
    slug = recipe.get('slug', '') or ''
    country = recipe.get('origin_country', '') or ''
    
    # A1. Check required fields
    required_fields = {
        'recipe_name': recipe_name,
        'ingredients': recipe.get('ingredients', []),
        'instructions': recipe.get('instructions', [])
    }
    
    # Check for description/summary (multiple possible fields)
    has_description = bool(
        recipe.get('history_summary') or 
        recipe.get('characteristic_profile') or 
        recipe.get('description') or
        recipe.get('origin_story')
    )
    
    missing_fields = []
    if not required_fields['recipe_name']:
        missing_fields.append('recipe_name')
    if not required_fields['ingredients'] or len(required_fields['ingredients']) == 0:
        missing_fields.append('ingredients')
    if not required_fields['instructions'] or len(required_fields['instructions']) == 0:
        missing_fields.append('instructions')
    if not has_description:
        missing_fields.append('description/summary')
    
    if missing_fields:
        flags.append(f"MISSING_FIELDS:{','.join(missing_fields)}")
    
    # A2. Check for placeholder/test content
    text_to_check = f"{recipe_name} {slug} {country}".lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            flags.append("PLACEHOLDER")
            break
    
    # Check suspicious countries
    if slug.lower() in SUSPICIOUS_COUNTRIES or country.lower() in SUSPICIOUS_COUNTRIES:
        if "PLACEHOLDER" not in flags:
            flags.append("PLACEHOLDER")
    
    # A3. Check for very short content
    description = recipe.get('history_summary', '') or recipe.get('characteristic_profile', '') or ''
    instructions = recipe.get('instructions', [])
    
    if description and len(description) < 50:
        flags.append("VERY_SHORT:description")
    
    if instructions and len(instructions) < 2:
        flags.append("VERY_SHORT:instructions")
    
    # A4. Duplicate detection (if all_recipes provided)
    if all_recipes:
        for other in all_recipes:
            if other.get('slug') == slug:
                continue  # Skip self
            
            other_name = other.get('recipe_name', '') or ''
            
            # Fuzzy match on recipe name
            if recipe_name and other_name:
                similarity = fuzz.ratio(recipe_name.lower(), other_name.lower())
                if similarity >= 88:
                    flags.append("POSSIBLE_DUPLICATE")
                    duplicate_of = other.get('slug')
                    break
            
            # Same slug base check
            slug_base = slug.rsplit('-', 1)[0] if '-' in slug else slug
            other_slug_base = other.get('slug', '').rsplit('-', 1)[0] if '-' in other.get('slug', '') else other.get('slug', '')
            
            if slug_base and other_slug_base and slug_base == other_slug_base and slug != other.get('slug'):
                if "POSSIBLE_DUPLICATE" not in [f.split(':')[0] for f in flags]:
                    flags.append("POSSIBLE_DUPLICATE")
                    duplicate_of = other.get('slug')
                    break
    
    # Determine if safe to publish
    blocking_flags = ['MISSING_FIELDS', 'PLACEHOLDER', 'POSSIBLE_DUPLICATE']
    is_safe = not any(f.split(':')[0] in blocking_flags for f in flags)
    
    # Bonus: prefer json_import source
    source = recipe.get('collection_method', '') or recipe.get('gpt_used', '') or 'unknown'
    
    return {
        'flags': flags,
        'duplicate_of': duplicate_of,
        'is_safe_to_publish': is_safe,
        'source': source
    }


@admin_router.get("/review-queue")
async def get_review_queue(
    include_hidden_published: int = Query(default=1, description="Include published but hidden recipes (1=yes)"),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Get all recipes that need review:
    1. status != "published" (unpublished/draft)
    2. status == "published" but missing required fields (hidden from public)
    
    Returns recipes with: flags, duplicate_of, is_safe_to_publish, source
    """
    # Get all non-published recipes
    non_published = await db.recipes.find(
        {"status": {"$ne": "published"}},
        {"_id": 0}
    ).sort("date_fetched", -1).to_list(1000)
    
    # Get published but hidden recipes (missing required fields)
    hidden_published = []
    if include_hidden_published == 1:
        published_recipes = await db.recipes.find(
            {"status": "published"},
            {"_id": 0}
        ).to_list(2000)
        
        for recipe in published_recipes:
            origin_country = recipe.get("origin_country", "") or ""
            continent = recipe.get("continent", "") or ""
            recipe_name = recipe.get("recipe_name", "") or ""
            ingredients = recipe.get("ingredients", []) or []
            instructions = recipe.get("instructions", []) or []
            
            is_hidden = (
                not origin_country or
                not continent or
                not recipe_name or
                not ingredients or len(ingredients) == 0 or
                not instructions or len(instructions) == 0
            )
            
            if is_hidden:
                # Check for invalid country
                invalid_country = False
                if origin_country and not is_valid_country(origin_country):
                    normalized = normalize_country(origin_country)
                    if normalized != origin_country:
                        invalid_country = True
                
                recipe["_hidden_reason"] = {
                    "missing_country": not origin_country,
                    "missing_continent": not continent,
                    "missing_name": not recipe_name,
                    "missing_ingredients": not ingredients or len(ingredients) == 0,
                    "missing_instructions": not instructions or len(instructions) == 0,
                    "invalid_country": invalid_country
                }
                hidden_published.append(recipe)
    
    # Get all recipes for duplicate detection
    all_recipes = await db.recipes.find({}, {"_id": 0, "recipe_name": 1, "slug": 1}).to_list(2000)
    
    # Process each recipe
    queue_items = []
    safe_count = 0
    blocked_count = 0
    duplicate_count = 0
    placeholder_count = 0
    hidden_published_count = 0
    
    # Process non-published recipes
    for recipe in non_published:
        detection = detect_flags(recipe, all_recipes)
        
        item = {
            'slug': recipe.get('slug', ''),
            'recipe_name': recipe.get('recipe_name', ''),
            'origin_country': recipe.get('origin_country', ''),
            'status': recipe.get('status', 'unknown'),
            'source': detection['source'],
            'flags': detection['flags'],
            'duplicate_of': detection['duplicate_of'],
            'is_safe_to_publish': detection['is_safe_to_publish'],
            'created_at': recipe.get('date_fetched', ''),
            'authenticity_level': recipe.get('authenticity_level', 0),
            'category': 'unpublished'
        }
        
        queue_items.append(item)
        
        if detection['is_safe_to_publish']:
            safe_count += 1
        else:
            blocked_count += 1
        
        if 'POSSIBLE_DUPLICATE' in [f.split(':')[0] for f in detection['flags']]:
            duplicate_count += 1
        
        if 'PLACEHOLDER' in detection['flags']:
            placeholder_count += 1
    
    # Process hidden published recipes
    for recipe in hidden_published:
        hidden_reason = recipe.get("_hidden_reason", {})
        flags = ["PUBLISHED_BUT_HIDDEN"]
        
        if hidden_reason.get("missing_country"):
            flags.append("MISSING_FIELDS:origin_country")
        if hidden_reason.get("missing_continent"):
            flags.append("MISSING_FIELDS:continent")
        if hidden_reason.get("missing_name"):
            flags.append("MISSING_FIELDS:recipe_name")
        if hidden_reason.get("missing_ingredients"):
            flags.append("MISSING_FIELDS:ingredients")
        if hidden_reason.get("missing_instructions"):
            flags.append("MISSING_FIELDS:instructions")
        if hidden_reason.get("invalid_country"):
            flags.append("INVALID_COUNTRY")
        
        item = {
            'slug': recipe.get('slug', ''),
            'recipe_name': recipe.get('recipe_name', ''),
            'origin_country': recipe.get('origin_country', ''),
            'status': 'published (hidden)',
            'source': recipe.get('collection_method', '') or 'unknown',
            'flags': flags,
            'duplicate_of': None,
            'is_safe_to_publish': False,  # Needs fix, not publish
            'created_at': recipe.get('date_fetched', ''),
            'authenticity_level': recipe.get('authenticity_level', 0),
            'category': 'hidden_published'
        }
        
        queue_items.append(item)
        hidden_published_count += 1
        blocked_count += 1
    
    return {
        'queue': queue_items,
        'total': len(queue_items),
        'counts': {
            'safe': safe_count,
            'blocked': blocked_count,
            'duplicates': duplicate_count,
            'placeholders': placeholder_count,
            'hidden_published': hidden_published_count
        }
    }


@admin_router.post("/recipes/bulk-publish")
async def bulk_publish_recipes(
    safe: int = Query(default=1, description="Only publish safe recipes (1=yes, 0=no)"),
    dry_run: int = Query(default=0, description="Preview only, no DB writes (1=yes, 0=no)"),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Bulk publish recipes.
    
    Query params:
    - safe=1: Only publish recipes that pass all safety checks
    - dry_run=1: Preview what would be published without making changes
    """
    # Get all non-published recipes
    non_published = await db.recipes.find(
        {"status": {"$ne": "published"}},
        {"_id": 0}
    ).to_list(1000)
    
    # Get all recipes for duplicate detection
    all_recipes = await db.recipes.find({}, {"_id": 0, "recipe_name": 1, "slug": 1}).to_list(2000)
    
    would_publish = []
    blocked = []
    
    for recipe in non_published:
        slug = recipe.get('slug', '')
        
        if safe == 1:
            detection = detect_flags(recipe, all_recipes)
            if detection['is_safe_to_publish']:
                would_publish.append(slug)
            else:
                blocked.append({
                    'slug': slug,
                    'reason': detection['flags']
                })
        else:
            # Publish all (dangerous!)
            would_publish.append(slug)
    
    # If dry run, return preview
    if dry_run == 1:
        return {
            'success': True,
            'dry_run': True,
            'would_publish_count': len(would_publish),
            'blocked_count': len(blocked),
            'sample_slugs': would_publish[:20],  # First 20 as sample
            'blocked_samples': blocked[:10]
        }
    
    # Actually publish
    published_count = 0
    for slug in would_publish:
        result = await db.recipes.update_one(
            {"slug": slug},
            {"$set": {
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        if result.modified_count > 0:
            published_count += 1
    
    logger.info(f"Bulk published {published_count} recipes")
    
    return {
        'success': True,
        'dry_run': False,
        'published_count': published_count,
        'blocked_count': len(blocked),
        'published_slugs': would_publish,
        'blocked_slugs': [b['slug'] for b in blocked]
    }


@admin_router.patch("/recipes/{slug}")
async def patch_recipe_status(
    slug: str,
    update: RecipeStatusUpdate,
    authorized: bool = Depends(verify_admin_token)
):
    """
    Update recipe status or archived flag.
    
    Body:
    - status: 'published', 'unpublished', 'draft', 'archived'
    - archived: true/false
    """
    # Build update document
    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if update.status is not None:
        update_doc["status"] = update.status
    
    if update.archived is not None:
        update_doc["archived"] = update.archived
        if update.archived:
            update_doc["status"] = "archived"
    
    if len(update_doc) == 1:  # Only has updated_at
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    result = await db.recipes.update_one(
        {"slug": slug},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return {
        "success": True,
        "slug": slug,
        "updated": update_doc
    }


# ============== AUDIT ROUTES ==============

# Import country normalization utilities
from utils.country_normalization import (
    normalize_country, get_continent, is_valid_country, 
    COUNTRY_NORMALIZATION, COUNTRY_TO_CONTINENT, COUNTRY_LABELS
)


@admin_router.get("/audit/visibility")
async def audit_visibility(authorized: bool = Depends(verify_admin_token)):
    """
    Comprehensive visibility audit for published recipes.
    Returns exact counts and breakdown of why recipes are hidden.
    """
    
    # Total documents
    total_docs = await db.recipes.count_documents({})
    
    # Published total
    published_total = await db.recipes.count_documents({"status": "published"})
    
    # Get all published recipes for detailed analysis
    published_recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0, "slug": 1, "recipe_name": 1, "origin_country": 1, "continent": 1,
         "ingredients": 1, "instructions": 1, "history_summary": 1, 
         "characteristic_profile": 1, "description": 1}
    ).to_list(2000)
    
    # Analyze each recipe for visibility issues
    reasons = {
        "missing_origin_country": [],
        "missing_continent": [],
        "missing_recipe_name": [],
        "missing_ingredients": [],
        "missing_instructions": [],
        "invalid_country_value": [],  # e.g., "Italia" instead of "Italy"
    }
    
    visible_count = 0
    hidden_slugs = []
    
    for recipe in published_recipes:
        slug = recipe.get("slug", "")
        issues = []
        
        # Check origin_country
        origin_country = recipe.get("origin_country", "") or ""
        if not origin_country:
            reasons["missing_origin_country"].append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "current_value": None
            })
            issues.append("MISSING_COUNTRY")
        elif not is_valid_country(origin_country):
            # Check if it's a localized variant
            normalized = normalize_country(origin_country)
            if normalized != origin_country and is_valid_country(normalized):
                reasons["invalid_country_value"].append({
                    "slug": slug,
                    "recipe_name": recipe.get("recipe_name", ""),
                    "current_value": origin_country,
                    "should_be": normalized
                })
                issues.append("INVALID_COUNTRY")
        
        # Check continent
        continent = recipe.get("continent", "") or ""
        if not continent:
            reasons["missing_continent"].append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "origin_country": origin_country,
                "derivable_continent": get_continent(origin_country) if origin_country else None
            })
            issues.append("MISSING_CONTINENT")
        
        # Check recipe_name
        if not recipe.get("recipe_name"):
            reasons["missing_recipe_name"].append({
                "slug": slug,
                "current_value": recipe.get("recipe_name")
            })
            issues.append("MISSING_NAME")
        
        # Check ingredients
        ingredients = recipe.get("ingredients", []) or []
        if not ingredients or len(ingredients) == 0:
            reasons["missing_ingredients"].append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", "")
            })
            issues.append("MISSING_INGREDIENTS")
        
        # Check instructions
        instructions = recipe.get("instructions", []) or []
        if not instructions or len(instructions) == 0:
            reasons["missing_instructions"].append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", "")
            })
            issues.append("MISSING_INSTRUCTIONS")
        
        if issues:
            hidden_slugs.append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "origin_country": origin_country,
                "issues": issues
            })
        else:
            visible_count += 1
    
    hidden_published_total = published_total - visible_count
    
    return {
        "summary": {
            "total_docs": total_docs,
            "published_total": published_total,
            "visible_total": visible_count,
            "hidden_published_total": hidden_published_total
        },
        "breakdown": {
            "missing_origin_country": len(reasons["missing_origin_country"]),
            "missing_continent": len(reasons["missing_continent"]),
            "missing_recipe_name": len(reasons["missing_recipe_name"]),
            "missing_ingredients": len(reasons["missing_ingredients"]),
            "missing_instructions": len(reasons["missing_instructions"]),
            "invalid_country_value": len(reasons["invalid_country_value"])
        },
        "details": {
            "missing_origin_country": reasons["missing_origin_country"][:50],
            "missing_continent": reasons["missing_continent"][:50],
            "missing_recipe_name": reasons["missing_recipe_name"][:50],
            "missing_ingredients": reasons["missing_ingredients"][:50],
            "missing_instructions": reasons["missing_instructions"][:50],
            "invalid_country_value": reasons["invalid_country_value"][:50]
        },
        "hidden_published_recipes": hidden_slugs[:50]
    }


@admin_router.post("/recipes/fix-visibility")
async def fix_visibility(
    dry_run: int = Query(default=1, description="Preview only (1) or execute (0)"),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Auto-fix visibility issues for published recipes.
    
    Fixes:
    1. Normalize country names (Italia -> Italy)
    2. Backfill continent from country
    3. Backfill recipe_name from translations if missing
    4. Mark incomplete recipes as unpublished
    
    Query params:
    - dry_run=1: Preview what would be fixed
    - dry_run=0: Execute fixes
    """
    
    # Get all published recipes
    published_recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0}
    ).to_list(2000)
    
    fixes = {
        "country_normalized": [],
        "continent_backfilled": [],
        "name_backfilled": [],
        "unpublished_incomplete": []
    }
    
    for recipe in published_recipes:
        slug = recipe.get("slug", "")
        updates = {}
        
        # 1. Normalize country
        origin_country = recipe.get("origin_country", "") or ""
        if origin_country:
            normalized = normalize_country(origin_country)
            if normalized != origin_country and is_valid_country(normalized):
                updates["origin_country"] = normalized
                fixes["country_normalized"].append({
                    "slug": slug,
                    "from": origin_country,
                    "to": normalized
                })
                origin_country = normalized  # Use normalized for continent lookup
        
        # 2. Backfill continent
        continent = recipe.get("continent", "") or ""
        if not continent and origin_country:
            derived_continent = get_continent(origin_country)
            if derived_continent:
                updates["continent"] = derived_continent
                fixes["continent_backfilled"].append({
                    "slug": slug,
                    "country": origin_country,
                    "continent": derived_continent
                })
        
        # 3. Backfill recipe_name
        recipe_name = recipe.get("recipe_name", "") or ""
        if not recipe_name:
            # Try to get from translations
            translations = recipe.get("translations", {})
            for lang in ["en", "it", "fr", "es", "de"]:
                trans = translations.get(lang, {})
                if trans.get("recipe_name"):
                    updates["recipe_name"] = trans.get("recipe_name")
                    fixes["name_backfilled"].append({
                        "slug": slug,
                        "from_lang": lang,
                        "name": trans.get("recipe_name")
                    })
                    break
            
            # If still no name, try title fields
            if "recipe_name" not in updates:
                fallback_name = (recipe.get("title_original") or 
                                recipe.get("title") or 
                                slug.replace("-", " ").title())
                if fallback_name:
                    updates["recipe_name"] = fallback_name
                    fixes["name_backfilled"].append({
                        "slug": slug,
                        "from_field": "fallback",
                        "name": fallback_name
                    })
        
        # 4. Check if still incomplete (must unpublish)
        ingredients = recipe.get("ingredients", []) or []
        instructions = recipe.get("instructions", []) or []
        
        is_incomplete = (
            (not recipe.get("recipe_name") and "recipe_name" not in updates) or
            not ingredients or len(ingredients) == 0 or
            not instructions or len(instructions) == 0
        )
        
        if is_incomplete:
            updates["status"] = "unpublished"
            updates["unpublish_reason"] = "incomplete_required_fields"
            fixes["unpublished_incomplete"].append({
                "slug": slug,
                "missing": {
                    "name": not recipe.get("recipe_name") and "recipe_name" not in updates,
                    "ingredients": not ingredients or len(ingredients) == 0,
                    "instructions": not instructions or len(instructions) == 0
                }
            })
        
        # Apply updates if not dry run
        if updates and dry_run == 0:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.recipes.update_one(
                {"slug": slug},
                {"$set": updates}
            )
    
    # Calculate summary
    total_fixes = (len(fixes["country_normalized"]) + 
                   len(fixes["continent_backfilled"]) + 
                   len(fixes["name_backfilled"]))
    
    return {
        "success": True,
        "dry_run": dry_run == 1,
        "summary": {
            "total_recipes_analyzed": len(published_recipes),
            "total_fixes_applied": total_fixes if dry_run == 0 else 0,
            "would_fix": total_fixes,
            "would_unpublish": len(fixes["unpublished_incomplete"])
        },
        "fixes": {
            "country_normalized": {
                "count": len(fixes["country_normalized"]),
                "samples": fixes["country_normalized"][:20]
            },
            "continent_backfilled": {
                "count": len(fixes["continent_backfilled"]),
                "samples": fixes["continent_backfilled"][:20]
            },
            "name_backfilled": {
                "count": len(fixes["name_backfilled"]),
                "samples": fixes["name_backfilled"][:20]
            },
            "unpublished_incomplete": {
                "count": len(fixes["unpublished_incomplete"]),
                "samples": fixes["unpublished_incomplete"][:20]
            }
        }
    }


@admin_router.get("/audit/public-visibility")
async def audit_public_visibility(authorized: bool = Depends(verify_admin_token)):
    """
    Audit public visibility of recipes.
    Returns counts and lists of recipes that are 'published' but may not appear on public site.
    """
    
    # Total documents
    total_docs = await db.recipes.count_documents({})
    
    # Status breakdown
    status_published = await db.recipes.count_documents({"status": "published"})
    status_not_published = await db.recipes.count_documents({"status": {"$ne": "published"}})
    status_missing = await db.recipes.count_documents({
        "$or": [
            {"status": {"$exists": False}},
            {"status": None}
        ]
    })
    
    # Published with required fields for public visibility
    published_with_continent = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$exists": True, "$ne": None, "$ne": ""}
    })
    
    published_missing_continent = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"continent": {"$exists": False}},
            {"continent": None},
            {"continent": ""}
        ]
    })
    
    published_with_country = await db.recipes.count_documents({
        "status": "published",
        "origin_country": {"$exists": True, "$ne": None, "$ne": ""}
    })
    
    published_missing_country = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"origin_country": {"$exists": False}},
            {"origin_country": None},
            {"origin_country": ""}
        ]
    })
    
    # Check for required fields (name, summary, ingredients, instructions)
    published_missing_required = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"recipe_name": {"$exists": False}},
            {"recipe_name": None},
            {"recipe_name": ""},
            {"ingredients": {"$exists": False}},
            {"ingredients": None},
            {"ingredients": {"$size": 0}},
            {"instructions": {"$exists": False}},
            {"instructions": None},
            {"instructions": {"$size": 0}}
        ]
    })
    
    # Get list of published recipes with visibility issues
    visibility_issues = []
    
    # Missing continent
    missing_continent_list = await db.recipes.find(
        {
            "status": "published",
            "$or": [
                {"continent": {"$exists": False}},
                {"continent": None},
                {"continent": ""}
            ]
        },
        {"slug": 1, "recipe_name": 1, "origin_country": 1, "_id": 0}
    ).limit(50).to_list(50)
    
    for r in missing_continent_list:
        visibility_issues.append({
            "slug": r.get("slug"),
            "recipe_name": r.get("recipe_name"),
            "origin_country": r.get("origin_country"),
            "reason": "MISSING_CONTINENT"
        })
    
    # Missing country
    missing_country_list = await db.recipes.find(
        {
            "status": "published",
            "$or": [
                {"origin_country": {"$exists": False}},
                {"origin_country": None},
                {"origin_country": ""}
            ]
        },
        {"slug": 1, "recipe_name": 1, "continent": 1, "_id": 0}
    ).limit(50).to_list(50)
    
    for r in missing_country_list:
        if r.get("slug") not in [v["slug"] for v in visibility_issues]:
            visibility_issues.append({
                "slug": r.get("slug"),
                "recipe_name": r.get("recipe_name"),
                "continent": r.get("continent"),
                "reason": "MISSING_COUNTRY"
            })
    
    # Missing required fields
    missing_required_list = await db.recipes.find(
        {
            "status": "published",
            "$or": [
                {"recipe_name": {"$exists": False}},
                {"recipe_name": None},
                {"recipe_name": ""},
                {"ingredients": {"$exists": False}},
                {"ingredients": None},
                {"ingredients": {"$size": 0}},
                {"instructions": {"$exists": False}},
                {"instructions": None},
                {"instructions": {"$size": 0}}
            ]
        },
        {"slug": 1, "recipe_name": 1, "origin_country": 1, "_id": 0}
    ).limit(50).to_list(50)
    
    for r in missing_required_list:
        if r.get("slug") not in [v["slug"] for v in visibility_issues]:
            visibility_issues.append({
                "slug": r.get("slug"),
                "recipe_name": r.get("recipe_name"),
                "origin_country": r.get("origin_country"),
                "reason": "MISSING_REQUIRED_FIELDS"
            })
    
    # Calculate truly visible (published AND has all required fields)
    truly_visible = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$exists": True, "$ne": None, "$ne": ""},
        "origin_country": {"$exists": True, "$ne": None, "$ne": ""},
        "recipe_name": {"$exists": True, "$ne": None, "$ne": ""},
        "ingredients": {"$exists": True, "$ne": None, "$not": {"$size": 0}},
        "instructions": {"$exists": True, "$ne": None, "$not": {"$size": 0}}
    })
    
    return {
        "summary": {
            "total_docs": total_docs,
            "status_published": status_published,
            "status_not_published": status_not_published,
            "status_missing": status_missing,
            "truly_visible_on_public": truly_visible,
            "gap": status_published - truly_visible
        },
        "published_breakdown": {
            "with_continent": published_with_continent,
            "missing_continent": published_missing_continent,
            "with_country": published_with_country,
            "missing_country": published_missing_country,
            "missing_required_fields": published_missing_required
        },
        "visibility_issues": visibility_issues[:50],
        "visibility_issues_count": len(visibility_issues)
    }



@admin_router.post("/recipes/deduplicate")
async def deduplicate_recipes(
    dry_run: int = Query(default=1, description="Preview only (1) or execute (0)"),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Find and remove duplicate recipes by slug.
    Keeps the recipe with the most ingredients and deletes the rest.
    
    Query params:
    - dry_run=1: Preview what would be deleted
    - dry_run=0: Execute deletions
    """
    
    # Find all duplicate slugs
    pipeline = [
        {"$group": {
            "_id": "$slug",
            "count": {"$sum": 1},
            "docs": {"$push": {
                "recipe_name": "$recipe_name",
                "ingredients_count": {"$size": {"$ifNull": ["$ingredients", []]}},
                "instructions_count": {"$size": {"$ifNull": ["$instructions", []]}},
                "status": "$status",
                "date_fetched": "$date_fetched"
            }}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    duplicates = await db.recipes.aggregate(pipeline).to_list(100)
    
    deletions = []
    kept = []
    
    for dup in duplicates:
        slug = dup["_id"]
        docs = dup["docs"]
        
        # Sort by ingredients count (descending), then by instructions count
        docs_sorted = sorted(docs, key=lambda x: (x.get("ingredients_count", 0), x.get("instructions_count", 0)), reverse=True)
        
        # Keep the best one (most complete)
        best = docs_sorted[0]
        kept.append({
            "slug": slug,
            "kept": {
                "recipe_name": best.get("recipe_name"),
                "ingredients_count": best.get("ingredients_count"),
                "instructions_count": best.get("instructions_count")
            }
        })
        
        # Mark others for deletion
        for doc in docs_sorted[1:]:
            deletions.append({
                "slug": slug,
                "recipe_name": doc.get("recipe_name"),
                "ingredients_count": doc.get("ingredients_count"),
                "instructions_count": doc.get("instructions_count"),
                "reason": "duplicate_slug"
            })
    
    # Execute deletions if not dry run
    deleted_count = 0
    if dry_run == 0 and deletions:
        for slug in set(d["slug"] for d in deletions):
            # Get all docs with this slug, sorted by completeness
            docs = await db.recipes.find(
                {"slug": slug},
                {"_id": 1, "ingredients": 1, "instructions": 1}
            ).to_list(100)
            
            # Sort by completeness
            docs_sorted = sorted(docs, key=lambda x: (
                len(x.get("ingredients", []) or []),
                len(x.get("instructions", []) or [])
            ), reverse=True)
            
            # Delete all except the first (most complete)
            for doc in docs_sorted[1:]:
                result = await db.recipes.delete_one({"_id": doc["_id"]})
                deleted_count += result.deleted_count
    
    return {
        "success": True,
        "dry_run": dry_run == 1,
        "summary": {
            "duplicate_slugs_found": len(duplicates),
            "total_duplicates_to_delete": len(deletions),
            "deleted_count": deleted_count if dry_run == 0 else 0
        },
        "kept": kept[:20],
        "deletions": deletions[:50]
    }



@admin_router.post("/recipes/normalize-continents")
async def normalize_continents(
    dry_run: int = Query(default=1, description="Preview only (1) or execute (0)"),
    authorized: bool = Depends(verify_admin_token)
):
    """
    Normalize all continent values to canonical set:
    Europe, Asia, Americas, Africa, Middle East, Oceania
    
    - Converts North/South America -> Americas
    - Converts compound values (Europe / Oceania) -> primary
    - Infers continent from country when Unknown
    
    Query params:
    - dry_run=1: Preview what would be changed
    - dry_run=0: Execute changes
    """
    
    VALID_CONTINENTS = ["Europe", "Asia", "Americas", "Africa", "Middle East", "Oceania"]
    
    # Continent normalization map
    CONTINENT_NORMALIZATION = {
        "North America": "Americas",
        "South America": "Americas",
        "Central America": "Americas",
        "Caribbean": "Americas",
        "Latin America": "Americas",
        "Europe / Oceania": "Europe",
        "Nord Africa / Medio Oriente": "Africa",
        "Middle East / North Africa": "Middle East",
        "MENA": "Middle East",
        "North Africa": "Africa",
        "Southeast Asia": "Asia",
        "East Asia": "Asia",
        "South Asia": "Asia",
        "Central Asia": "Asia",
        "Western Europe": "Europe",
        "Eastern Europe": "Europe",
        "Southern Europe": "Europe",
        "Northern Europe": "Europe",
        "Sub-Saharan Africa": "Africa",
        "West Africa": "Africa",
        "East Africa": "Africa",
        "Oceana": "Oceania",
        "Australasia": "Oceania",
        "Pacific": "Oceania",
    }
    
    # Country to continent for inference
    COUNTRY_TO_CONTINENT = {
        # Europe
        "Italy": "Europe", "France": "Europe", "Spain": "Europe", "Germany": "Europe",
        "Portugal": "Europe", "Greece": "Europe", "United Kingdom": "Europe",
        "Ireland": "Europe", "Belgium": "Europe", "Netherlands": "Europe",
        "Switzerland": "Europe", "Austria": "Europe", "Poland": "Europe",
        "Czech Republic": "Europe", "Hungary": "Europe", "Romania": "Europe",
        "Bulgaria": "Europe", "Croatia": "Europe", "Slovenia": "Europe",
        "Slovakia": "Europe", "Serbia": "Europe", "Albania": "Europe",
        "Ukraine": "Europe", "Russia": "Europe", "Finland": "Europe",
        "Sweden": "Europe", "Norway": "Europe", "Denmark": "Europe",
        "Malta": "Europe", "Cyprus": "Europe",
        
        # Americas
        "United States": "Americas", "Mexico": "Americas", "Canada": "Americas",
        "Brazil": "Americas", "Argentina": "Americas", "Peru": "Americas",
        "Chile": "Americas", "Colombia": "Americas", "Venezuela": "Americas",
        "Ecuador": "Americas", "Bolivia": "Americas", "Cuba": "Americas",
        "Dominican Republic": "Americas", "Puerto Rico": "Americas",
        "Jamaica": "Americas", "Guatemala": "Americas", "Honduras": "Americas",
        "Costa Rica": "Americas", "Panama": "Americas",
        
        # Asia
        "Japan": "Asia", "China": "Asia", "India": "Asia", "Thailand": "Asia",
        "Vietnam": "Asia", "South Korea": "Asia", "Indonesia": "Asia",
        "Malaysia": "Asia", "Philippines": "Asia", "Singapore": "Asia",
        "Taiwan": "Asia", "Myanmar": "Asia", "Cambodia": "Asia",
        "Bangladesh": "Asia", "Pakistan": "Asia", "Sri Lanka": "Asia",
        "Nepal": "Asia", "Afghanistan": "Asia", "Kazakhstan": "Asia",
        "Mongolia": "Asia",
        
        # Middle East
        "Turkey": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
        "Syria": "Middle East", "Lebanon": "Middle East", "Jordan": "Middle East",
        "Israel": "Middle East", "Palestine": "Middle East",
        "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East",
        "Qatar": "Middle East", "Kuwait": "Middle East", "Bahrain": "Middle East",
        "Oman": "Middle East", "Yemen": "Middle East",
        "Armenia": "Middle East", "Georgia": "Middle East", "Azerbaijan": "Middle East",
        
        # Africa
        "Morocco": "Africa", "Egypt": "Africa", "Tunisia": "Africa",
        "Algeria": "Africa", "Libya": "Africa", "South Africa": "Africa",
        "Nigeria": "Africa", "Kenya": "Africa", "Ethiopia": "Africa",
        "Ghana": "Africa", "Senegal": "Africa", "Tanzania": "Africa",
        
        # Oceania
        "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
        "Papua New Guinea": "Oceania",
    }
    
    def get_canonical_continent(current: str, country: str) -> str:
        """Get canonical continent value."""
        if current in VALID_CONTINENTS:
            return current
        
        if current in CONTINENT_NORMALIZATION:
            return CONTINENT_NORMALIZATION[current]
        
        # Check for keywords
        if current:
            lower = current.lower()
            if "america" in lower:
                return "Americas"
            if "africa" in lower:
                return "Africa"
            if "asia" in lower:
                return "Asia"
            if "europe" in lower:
                return "Europe"
            if "oceania" in lower or "australia" in lower or "pacific" in lower:
                return "Oceania"
            if "middle east" in lower or "levant" in lower:
                return "Middle East"
        
        # Infer from country
        if country and country in COUNTRY_TO_CONTINENT:
            return COUNTRY_TO_CONTINENT[country]
        
        return None
    
    # Get all published recipes
    published_recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 1, "slug": 1, "recipe_name": 1, "continent": 1, "origin_country": 1}
    ).to_list(2000)
    
    changes = []
    failed = []
    already_valid = 0
    
    for recipe in published_recipes:
        recipe_id = recipe.get("_id")
        slug = recipe.get("slug", "")
        current_continent = recipe.get("continent", "") or ""
        country = recipe.get("origin_country", "") or ""
        
        if current_continent in VALID_CONTINENTS:
            already_valid += 1
            continue
        
        new_continent = get_canonical_continent(current_continent, country)
        
        if new_continent and new_continent in VALID_CONTINENTS:
            changes.append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "old_continent": current_continent or "(empty)",
                "new_continent": new_continent,
                "country": country,
                "inference": "country" if not current_continent or current_continent == "Unknown" else "mapping"
            })
            
            if dry_run == 0:
                await db.recipes.update_one(
                    {"_id": recipe_id},
                    {"$set": {
                        "continent": new_continent,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "migration_applied": "continent_normalization_v1"
                    }}
                )
        else:
            failed.append({
                "slug": slug,
                "recipe_name": recipe.get("recipe_name", ""),
                "current_continent": current_continent,
                "country": country
            })
    
    # Get post-migration counts
    continent_counts = {}
    for continent in VALID_CONTINENTS:
        count = await db.recipes.count_documents({
            "status": "published",
            "continent": continent
        })
        continent_counts[continent] = count
    
    invalid_remaining = await db.recipes.count_documents({
        "status": "published",
        "continent": {"$nin": VALID_CONTINENTS}
    })
    
    return {
        "success": True,
        "dry_run": dry_run == 1,
        "summary": {
            "total_published": len(published_recipes),
            "already_valid": already_valid,
            "normalized": len(changes) if dry_run == 0 else 0,
            "would_normalize": len(changes),
            "failed": len(failed),
            "invalid_remaining": invalid_remaining
        },
        "continent_counts": continent_counts,
        "changes": changes[:50],
        "failed": failed[:20]
    }



# ============== AI IMAGE BATCH GENERATION ==============

# In-memory job state (single-worker safe)
_image_job: Dict[str, Any] = {
    "running": False,
    "total": 0,
    "generated": 0,
    "failed": 0,
    "skipped": 0,
    "current_slug": None,
    "cost_estimate_usd": 0.0,
    "log": [],
    "started_at": None,
    "finished_at": None,
}

COST_PER_IMAGE = 0.04


async def _run_image_batch(batch_size: int):
    """Background coroutine that generates images for all missing recipes."""
    from services.ai_image_service import generate_recipe_image, STATIC_DIR, _build_alt
    import asyncio

    _image_job["running"] = True
    _image_job["generated"] = 0
    _image_job["failed"] = 0
    _image_job["skipped"] = 0
    _image_job["cost_estimate_usd"] = 0.0
    _image_job["log"] = []
    _image_job["started_at"] = datetime.now(timezone.utc).isoformat()
    _image_job["finished_at"] = None

    missing = await db.recipes.find(
        {
            "status": "published",
            "$or": [
                {"image_url": {"$exists": False}},
                {"image_url": None},
                {"image_url": ""},
            ],
        },
        {"_id": 0, "slug": 1, "recipe_name": 1, "origin_country": 1},
    ).to_list(500)

    _image_job["total"] = len(missing)

    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]

        for recipe_stub in batch:
            slug = recipe_stub["slug"]
            _image_job["current_slug"] = slug

            # Skip if file on disk already
            found_on_disk = False
            for ext in (".webp", ".png"):
                if (STATIC_DIR / f"{slug}{ext}").exists():
                    url = f"/api/recipe-images/{slug}{ext}"
                    full_recipe = await db.recipes.find_one({"slug": slug}, {"_id": 0})
                    await db.recipes.update_one(
                        {"slug": slug},
                        {"$set": {
                            "image_url": url,
                            "image_alt": _build_alt(full_recipe or recipe_stub),
                            "image_source": "ai",
                        }},
                    )
                    _image_job["skipped"] += 1
                    _image_job["log"].append(f"SKIP {slug} (file exists)")
                    found_on_disk = True
                    break

            if found_on_disk:
                continue

            full_recipe = await db.recipes.find_one(
                {"slug": slug, "status": "published"}, {"_id": 0}
            )
            if not full_recipe:
                _image_job["skipped"] += 1
                _image_job["log"].append(f"SKIP {slug} (not found)")
                continue

            try:
                result = await generate_recipe_image(full_recipe)
                if result:
                    await db.recipes.update_one(
                        {"slug": slug},
                        {"$set": {
                            "image_url": result["url"],
                            "image_alt": result["alt"],
                            "image_source": result["source"],
                            "image_metadata": result["metadata"],
                        }},
                    )
                    _image_job["generated"] += 1
                    _image_job["cost_estimate_usd"] = round(
                        _image_job["generated"] * COST_PER_IMAGE, 2
                    )
                    _image_job["log"].append(f"OK {slug} ~${COST_PER_IMAGE}")
                    logger.info(f"Batch: generated {slug} (~${COST_PER_IMAGE})")
                else:
                    _image_job["failed"] += 1
                    _image_job["log"].append(f"FAIL {slug} (no image returned)")
            except Exception as e:
                _image_job["failed"] += 1
                _image_job["log"].append(f"FAIL {slug}: {str(e)[:120]}")
                logger.error(f"Batch image gen failed for {slug}: {e}")

        # Pause between batches
        if i + batch_size < len(missing):
            await asyncio.sleep(2)

    _image_job["current_slug"] = None
    _image_job["running"] = False
    _image_job["finished_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"Image batch complete: {_image_job['generated']} generated, "
        f"{_image_job['failed']} failed, {_image_job['skipped']} skipped"
    )


@admin_router.post("/images/generate-batch")
async def generate_batch_images(
    authorized: bool = Depends(verify_admin_token),
    batch_size: int = Query(5, ge=1, le=10, description="Recipes per batch"),
    dry_run: bool = Query(False, description="Preview without generating"),
):
    """
    Batch-generate AI images for all recipes missing image_url.

    - Admin-only
    - Runs in background (returns immediately)
    - Processes in batches (default 5)
    - Check progress via GET /api/admin/images/status
    - Skips recipes that already have image_url or file on disk
    - Graceful failure per recipe (continues on error)
    """
    import asyncio

    missing_count = await db.recipes.count_documents({
        "status": "published",
        "$or": [
            {"image_url": {"$exists": False}},
            {"image_url": None},
            {"image_url": ""},
        ],
    })

    estimated_cost = round(missing_count * COST_PER_IMAGE, 2)

    if dry_run:
        recipes = await db.recipes.find(
            {
                "status": "published",
                "$or": [
                    {"image_url": {"$exists": False}},
                    {"image_url": None},
                    {"image_url": ""},
                ],
            },
            {"_id": 0, "slug": 1, "recipe_name": 1},
        ).to_list(500)
        return {
            "dry_run": True,
            "recipes_missing_images": missing_count,
            "estimated_cost_usd": estimated_cost,
            "batch_size": batch_size,
            "recipes": [
                {"slug": r["slug"], "name": r.get("recipe_name", "?")}
                for r in recipes
            ],
        }

    if _image_job["running"]:
        return {
            "started": False,
            "message": "A batch job is already running. Check GET /api/admin/images/status",
        }

    # Fire and forget
    asyncio.create_task(_run_image_batch(batch_size))

    return {
        "started": True,
        "recipes_to_process": missing_count,
        "estimated_cost_usd": estimated_cost,
        "batch_size": batch_size,
        "message": "Background job started. Check GET /api/admin/images/status for progress.",
    }


@admin_router.get("/images/status")
async def get_image_job_status(
    authorized: bool = Depends(verify_admin_token),
):
    """Get current status of the batch image generation job."""
    progress = 0
    done = _image_job["generated"] + _image_job["failed"] + _image_job["skipped"]
    if _image_job["total"] > 0:
        progress = round(done / _image_job["total"] * 100, 1)

    return {
        "running": _image_job["running"],
        "total": _image_job["total"],
        "progress_pct": progress,
        "generated": _image_job["generated"],
        "failed": _image_job["failed"],
        "skipped": _image_job["skipped"],
        "cost_estimate_usd": _image_job["cost_estimate_usd"],
        "current_slug": _image_job["current_slug"],
        "started_at": _image_job["started_at"],
        "finished_at": _image_job["finished_at"],
        "recent_log": _image_job["log"][-20:],
    }


@admin_router.post("/images/regenerate")
async def regenerate_single_image(
    slug: str = Query(..., description="Recipe slug to regenerate"),
    custom_prompt: Optional[str] = Query(None, description="Custom image prompt to save and use"),
    authorized: bool = Depends(verify_admin_token),
):
    """
    Regenerate the AI image for a single recipe.

    - Admin-only
    - Overwrites existing image file and DB fields
    - Optionally sets custom_image_prompt on the recipe
    - Does NOT trigger batch job or affect other recipes
    - Uses concurrency lock
    """
    from services.ai_image_service import generate_recipe_image, STATIC_DIR

    recipe = await db.recipes.find_one(
        {"slug": slug, "status": "published"}, {"_id": 0}
    )
    if not recipe:
        raise HTTPException(status_code=404, detail=f"Recipe not found: {slug}")

    # Save custom prompt to DB if provided
    if custom_prompt:
        await db.recipes.update_one(
            {"slug": slug},
            {"$set": {"custom_image_prompt": custom_prompt}},
        )
        recipe["custom_image_prompt"] = custom_prompt

    # Delete existing image file so generate_recipe_image creates a fresh one
    for ext in (".webp", ".png"):
        path = STATIC_DIR / f"{slug}{ext}"
        if path.exists():
            path.unlink()

    # Clear existing DB image fields so the generator runs
    await db.recipes.update_one(
        {"slug": slug},
        {"$unset": {"image_url": "", "image_alt": "", "image_source": "", "image_metadata": ""}},
    )

    result = await generate_recipe_image(recipe)

    if not result:
        return {
            "success": False,
            "slug": slug,
            "error": "Image generation failed. Check backend logs.",
        }

    update = {
        "image_url": result["url"],
        "image_alt": result["alt"],
        "image_source": result["source"],
        "image_metadata": result["metadata"],
    }
    await db.recipes.update_one({"slug": slug}, {"$set": update})

    return {
        "success": True,
        "slug": slug,
        "image_url": result["url"],
        "prompt_used": result["metadata"]["prompt_used"],
        "custom_prompt_saved": bool(custom_prompt),
    }
