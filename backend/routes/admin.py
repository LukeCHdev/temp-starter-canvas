# Admin Routes for Recipe Management

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import json
import logging
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

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
async def get_all_recipes(authorized: bool = Depends(verify_admin_token)):
    """Get all recipes for admin management."""
    recipes = await db.recipes.find(
        {},
        {"_id": 0}
    ).sort("date_fetched", -1).to_list(1000)
    
    return {
        "recipes": recipes,
        "total": len(recipes)
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
    """Import a recipe from JSON."""
    try:
        recipe_data = recipe.recipe_json
        
        # Validate required fields
        recipe_name = recipe_data.get('recipe_name', '')
        if not recipe_name:
            raise HTTPException(status_code=400, detail="recipe_name is required")
        
        # Get or generate slug
        origin_country = recipe_data.get('origin_country', '')
        slug = recipe_data.get('slug') or generate_slug(recipe_name, origin_country)
        
        # Check for duplicates
        existing = await db.recipes.find_one({"slug": slug})
        if existing:
            raise HTTPException(status_code=400, detail=f"Recipe with slug '{slug}' already exists")
        
        # Enrich the recipe data
        enriched_recipe = {
            **recipe_data,
            "slug": slug,
            "continent": recipe_data.get('continent') or get_continent(origin_country),
            "content_language": recipe_data.get('content_language', 'en'),  # Default to English
            "status": recipe_data.get('status', 'published'),
            "date_fetched": datetime.now(timezone.utc).isoformat(),
            "gpt_used": recipe_data.get('gpt_used', 'Manual Import'),
            "collection_method": recipe_data.get('collection_method', 'admin_import'),
            # Initialize analytics if not present
            "views_count": recipe_data.get('views_count', 0),
            "favorites_count": recipe_data.get('favorites_count', 0),
            "average_rating": recipe_data.get('average_rating', 0),
            "ratings_count": recipe_data.get('ratings_count', 0),
            "comments_count": recipe_data.get('comments_count', 0),
        }
        
        # Save to database
        await db.recipes.insert_one(enriched_recipe)
        
        return {
            "success": True,
            "slug": slug,
            "message": f"Recipe '{recipe_name}' imported successfully"
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

# ============== STATS ROUTES ==============

@admin_router.get("/stats")
async def get_admin_stats(authorized: bool = Depends(verify_admin_token)):
    """Get admin dashboard statistics."""
    total_recipes = await db.recipes.count_documents({})
    published_recipes = await db.recipes.count_documents({"status": "published"})
    
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
        {"_id": 0, "recipe_name": 1, "slug": 1, "date_fetched": 1}
    ).sort("date_fetched", -1).limit(5).to_list(5)
    
    return {
        "total_recipes": total_recipes,
        "published_recipes": published_recipes,
        "recipes_by_country": [{"country": c["_id"], "count": c["count"]} for c in countries if c["_id"]],
        "recipes_by_continent": [{"continent": c["_id"], "count": c["count"]} for c in continents if c["_id"]],
        "recent_recipes": recent
    }
