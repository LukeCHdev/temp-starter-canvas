# Document Import Routes for PDF/ODF Recipe Extraction

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import io
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

from services.document_import import (
    DocumentParser, 
    RecipeDetector, 
    ImportSession,
    process_recipe_with_ai,
    DEFAULT_BATCH_SIZE
)
from services.sous_chef_ai import sous_chef_ai
from models.recipe import validate_canonical_recipe, normalize_to_canonical
from thefuzz import fuzz

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

document_router = APIRouter(prefix="/api/admin/import", tags=["document-import"])

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME')]

# Admin password from environment
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


# ============== MODELS ==============

class DocumentURLImport(BaseModel):
    url: str
    country: str = "Unknown"  # Origin country for the document
    batch_size: int = DEFAULT_BATCH_SIZE

class ProcessBatchRequest(BaseModel):
    batch_size: int = DEFAULT_BATCH_SIZE

class RecipeEditRequest(BaseModel):
    recipe_data: Dict[str, Any]

class RecipeActionRequest(BaseModel):
    action: str  # 'approve', 'skip', 'edit'
    edited_data: Optional[Dict[str, Any]] = None


# ============== AUTH HELPER ==============

def verify_admin_token(authorization: str = Header(None)) -> bool:
    """Verify the admin token from header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = parts[1]
    
    import base64
    try:
        decoded = base64.b64decode(token).decode('utf-8')
        if decoded != ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True


# ============== HELPER FUNCTIONS ==============

def generate_slug(recipe_name: str, country: str = "") -> str:
    """Generate URL-friendly slug."""
    import re
    import unicodedata
    
    text = f"{recipe_name} {country}".strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    slug = text.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-') or 'recipe'


async def check_duplicate(recipe_name: str, country: str, db) -> Optional[Dict[str, Any]]:
    """Check if a similar recipe already exists.
    
    Returns the matching recipe if found, None otherwise.
    """
    # Get all recipes for fuzzy matching
    existing_recipes = await db.recipes.find(
        {"status": "published"},
        {"recipe_name": 1, "origin_country": 1, "slug": 1, "_id": 0}
    ).to_list(1000)
    
    for existing in existing_recipes:
        existing_name = existing.get('recipe_name', '')
        existing_country = existing.get('origin_country', '')
        
        # Check fuzzy match on name
        name_score = fuzz.token_set_ratio(recipe_name.lower(), existing_name.lower())
        
        # Higher threshold if same country
        if existing_country.lower() == country.lower():
            if name_score >= 80:
                return existing
        else:
            if name_score >= 90:
                return existing
    
    return None


def get_continent(country: str) -> str:
    """Get continent for a country."""
    COUNTRY_TO_CONTINENT = {
        "Chile": "Americas", "Argentina": "Americas", "Peru": "Americas", "Mexico": "Americas",
        "Brazil": "Americas", "Colombia": "Americas", "Venezuela": "Americas", "Ecuador": "Americas",
        "Bolivia": "Americas", "Paraguay": "Americas", "Uruguay": "Americas",
        "Italy": "Europe", "France": "Europe", "Spain": "Europe", "Germany": "Europe",
        "United Kingdom": "Europe", "Greece": "Europe", "Portugal": "Europe",
        "Japan": "Asia", "China": "Asia", "South Korea": "Asia", "Vietnam": "Asia",
        "Thailand": "Asia", "India": "Asia", "Indonesia": "Asia",
        "Morocco": "Africa", "Egypt": "Africa", "Ethiopia": "Africa",
        "Lebanon": "Middle East", "Israel": "Middle East", "Iran": "Middle East",
        "Australia": "Oceania", "New Zealand": "Oceania",
    }
    return COUNTRY_TO_CONTINENT.get(country, "Americas")


# ============== ENDPOINTS ==============

@document_router.post("/document-url")
async def import_from_url(request: DocumentURLImport, authorized: bool = Depends(verify_admin_token)):
    """Import recipes from a PDF/ODF document URL.
    
    Phase 1: Parse document and detect recipes.
    Returns session ID for further processing.
    """
    try:
        # Create import session
        session = ImportSession()
        session.document_url = request.url
        session.status = 'parsing'
        
        logger.info(f"Starting document import from URL: {request.url}")
        
        # Parse document
        try:
            text, doc_format = await DocumentParser.parse_from_url(request.url)
        except Exception as e:
            session.status = 'error'
            session.error_message = f"Failed to parse document: {str(e)}"
            await db.import_sessions.insert_one(session.to_dict())
            raise HTTPException(status_code=400, detail=str(e))
        
        # Detect language
        detected_language = DocumentParser.detect_language(text)
        session.document_language = detected_language
        
        logger.info(f"Document parsed: {len(text)} chars, language: {detected_language}, format: {doc_format}")
        
        # Detect recipes
        detected_recipes = RecipeDetector.detect_recipes(text, detected_language)
        
        if not detected_recipes:
            session.status = 'error'
            session.error_message = "No recipes detected in document"
            await db.import_sessions.insert_one(session.to_dict())
            raise HTTPException(status_code=400, detail="No recipes detected in document")
        
        # Initialize recipe entries
        session.recipes = []
        for i, recipe in enumerate(detected_recipes):
            session.recipes.append({
                'index': i,
                'title': recipe['title'],
                'raw_text': recipe['raw_text'],
                'status': 'pending',  # pending, processing, ready, approved, skipped, duplicate, saved, error
                'ai_result': None,
                'duplicate_match': None,
                'error_message': None,
                'origin_country': request.country
            })
        
        session.total_recipes = len(detected_recipes)
        session.status = 'detected'
        session.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Save session to database
        await db.import_sessions.insert_one(session.to_dict())
        
        logger.info(f"Session {session.session_id}: Detected {len(detected_recipes)} recipes")
        
        return {
            "success": True,
            "session_id": session.session_id,
            "document_language": detected_language,
            "total_recipes": len(detected_recipes),
            "recipes": [
                {
                    "index": r['index'],
                    "title": r['title'],
                    "status": r['status'],
                    "preview": r['raw_text'][:200] + "..." if len(r['raw_text']) > 200 else r['raw_text']
                }
                for r in session.recipes
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.post("/document")
async def import_from_file(
    file: UploadFile = File(...),
    country: str = "Unknown",
    authorized: bool = Depends(verify_admin_token)
):
    """Import recipes from uploaded PDF/ODF file."""
    try:
        # Validate file type
        filename = file.filename.lower()
        if not (filename.endswith('.pdf') or filename.endswith('.odt')):
            raise HTTPException(status_code=400, detail="File must be PDF or ODT format")
        
        # Read file content
        content = await file.read()
        file_obj = io.BytesIO(content)
        
        # Create import session
        session = ImportSession()
        session.document_url = f"upload://{file.filename}"
        session.status = 'parsing'
        
        # Parse document
        if filename.endswith('.pdf'):
            text = DocumentParser.parse_pdf(file_obj)
            doc_format = 'pdf'
        else:
            text = DocumentParser.parse_odf(file_obj)
            doc_format = 'odf'
        
        # Detect language
        detected_language = DocumentParser.detect_language(text)
        session.document_language = detected_language
        
        logger.info(f"File parsed: {len(text)} chars, language: {detected_language}")
        
        # Detect recipes
        detected_recipes = RecipeDetector.detect_recipes(text, detected_language)
        
        if not detected_recipes:
            raise HTTPException(status_code=400, detail="No recipes detected in document")
        
        # Initialize recipe entries
        session.recipes = []
        for i, recipe in enumerate(detected_recipes):
            session.recipes.append({
                'index': i,
                'title': recipe['title'],
                'raw_text': recipe['raw_text'],
                'status': 'pending',
                'ai_result': None,
                'duplicate_match': None,
                'error_message': None,
                'origin_country': country
            })
        
        session.total_recipes = len(detected_recipes)
        session.status = 'detected'
        session.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Save session
        await db.import_sessions.insert_one(session.to_dict())
        
        return {
            "success": True,
            "session_id": session.session_id,
            "document_language": detected_language,
            "total_recipes": len(detected_recipes),
            "recipes": [
                {
                    "index": r['index'],
                    "title": r['title'],
                    "status": r['status'],
                    "preview": r['raw_text'][:200] + "..."
                }
                for r in session.recipes
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.get("/session/{session_id}")
async def get_session(session_id: str, authorized: bool = Depends(verify_admin_token)):
    """Get import session status and details."""
    session_data = await db.import_sessions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_data


@document_router.post("/session/{session_id}/process")
async def process_batch(
    session_id: str,
    request: ProcessBatchRequest,
    authorized: bool = Depends(verify_admin_token)
):
    """Process the next batch of recipes with AI.
    
    Processes pending recipes and checks for duplicates.
    """
    # Get session
    session_data = await db.import_sessions.find_one({"session_id": session_id})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = ImportSession.from_dict(session_data)
    
    if session.status == 'completed':
        return {"message": "Session already completed", "session": session.to_dict()}
    
    # Find pending recipes
    pending_indices = [
        i for i, r in enumerate(session.recipes) 
        if r['status'] == 'pending'
    ]
    
    if not pending_indices:
        session.status = 'completed'
        await db.import_sessions.update_one(
            {"session_id": session_id},
            {"$set": session.to_dict()}
        )
        return {"message": "No pending recipes to process", "session": session.to_dict()}
    
    # Process batch
    batch_indices = pending_indices[:request.batch_size]
    session.status = 'processing'
    
    processed_results = []
    
    for idx in batch_indices:
        recipe_entry = session.recipes[idx]
        recipe_entry['status'] = 'processing'
        
        try:
            # Process with AI
            ai_result = await process_recipe_with_ai(
                raw_text=recipe_entry['raw_text'],
                title=recipe_entry['title'],
                language=session.document_language,
                country=recipe_entry['origin_country'],
                ai_service=sous_chef_ai
            )
            
            if ai_result:
                # Normalize to canonical schema
                normalized = normalize_to_canonical(ai_result)
                
                # Validate
                is_valid, errors = validate_canonical_recipe(normalized)
                
                if not is_valid:
                    recipe_entry['status'] = 'error'
                    recipe_entry['error_message'] = f"Validation failed: {'; '.join(errors)}"
                else:
                    # Check for duplicates
                    recipe_name = normalized.get('recipe_name', recipe_entry['title'])
                    country = normalized.get('origin_country', recipe_entry['origin_country'])
                    
                    duplicate = await check_duplicate(recipe_name, country, db)
                    
                    if duplicate:
                        recipe_entry['status'] = 'duplicate'
                        recipe_entry['duplicate_match'] = {
                            'name': duplicate.get('recipe_name'),
                            'country': duplicate.get('origin_country'),
                            'slug': duplicate.get('slug')
                        }
                    else:
                        recipe_entry['status'] = 'ready'
                    
                    recipe_entry['ai_result'] = normalized
            else:
                recipe_entry['status'] = 'error'
                recipe_entry['error_message'] = 'AI returned empty result'
        
        except Exception as e:
            recipe_entry['status'] = 'error'
            recipe_entry['error_message'] = str(e)
            logger.error(f"Error processing recipe {idx}: {str(e)}")
        
        session.processed_count += 1
        processed_results.append({
            'index': idx,
            'title': recipe_entry['title'],
            'status': recipe_entry['status'],
            'duplicate_match': recipe_entry.get('duplicate_match'),
            'error_message': recipe_entry.get('error_message')
        })
    
    # Update session
    session.status = 'detected' if any(r['status'] == 'pending' for r in session.recipes) else 'ready_for_review'
    session.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.import_sessions.update_one(
        {"session_id": session_id},
        {"$set": session.to_dict()}
    )
    
    return {
        "success": True,
        "processed": processed_results,
        "remaining": len([r for r in session.recipes if r['status'] == 'pending']),
        "session": session.to_dict()
    }


@document_router.post("/session/{session_id}/recipe/{recipe_index}/action")
async def recipe_action(
    session_id: str,
    recipe_index: int,
    request: RecipeActionRequest,
    authorized: bool = Depends(verify_admin_token)
):
    """Perform action on a recipe: approve, skip, or edit."""
    # Get session
    session_data = await db.import_sessions.find_one({"session_id": session_id})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = ImportSession.from_dict(session_data)
    
    if recipe_index < 0 or recipe_index >= len(session.recipes):
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe_entry = session.recipes[recipe_index]
    
    if request.action == 'skip':
        recipe_entry['status'] = 'skipped'
        session.skipped_count += 1
        
    elif request.action == 'approve':
        # Save the recipe to database
        recipe_data = recipe_entry.get('ai_result')
        if not recipe_data:
            raise HTTPException(status_code=400, detail="No recipe data to save")
        
        # Use edited data if provided
        if request.edited_data:
            recipe_data = request.edited_data
        
        # Generate slug
        recipe_name = recipe_data.get('recipe_name', recipe_entry['title'])
        country = recipe_data.get('origin_country', recipe_entry['origin_country'])
        slug = generate_slug(recipe_name, country)
        
        # Check if slug exists
        existing = await db.recipes.find_one({"slug": slug})
        if existing:
            # Append number to slug
            counter = 1
            while await db.recipes.find_one({"slug": f"{slug}-{counter}"}):
                counter += 1
            slug = f"{slug}-{counter}"
        
        # Prepare final recipe
        final_recipe = {
            **recipe_data,
            "slug": slug,
            "continent": get_continent(country),
            "content_language": session.document_language,
            "status": "published",
            "date_fetched": datetime.now(timezone.utc).isoformat(),
            "gpt_used": "Sous-Chef Linguine (Document Import)",
            "collection_method": "document_import",
            "source_document": session.document_url,
            "views_count": 0,
            "favorites_count": 0,
            "average_rating": 0,
            "ratings_count": 0,
            "comments_count": 0
        }
        
        # Save to database
        await db.recipes.insert_one(final_recipe)
        
        recipe_entry['status'] = 'saved'
        recipe_entry['saved_slug'] = slug
        session.saved_count += 1
        
        logger.info(f"Recipe saved: {recipe_name} -> {slug}")
        
    elif request.action == 'edit':
        # Just update the AI result with edited data
        if request.edited_data:
            # Validate edited data
            is_valid, errors = validate_canonical_recipe(request.edited_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid data: {'; '.join(errors)}")
            
            recipe_entry['ai_result'] = request.edited_data
            recipe_entry['status'] = 'ready'
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
    
    # Update session
    session.updated_at = datetime.now(timezone.utc).isoformat()
    
    # Check if all recipes are processed
    all_done = all(r['status'] in ['saved', 'skipped', 'error'] for r in session.recipes)
    if all_done:
        session.status = 'completed'
    
    await db.import_sessions.update_one(
        {"session_id": session_id},
        {"$set": session.to_dict()}
    )
    
    return {
        "success": True,
        "recipe_status": recipe_entry['status'],
        "session": session.to_dict()
    }


@document_router.post("/session/{session_id}/approve-all")
async def approve_all_ready(session_id: str, authorized: bool = Depends(verify_admin_token)):
    """Approve and save all recipes with 'ready' status."""
    session_data = await db.import_sessions.find_one({"session_id": session_id})
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = ImportSession.from_dict(session_data)
    
    saved = []
    errors = []
    
    for i, recipe_entry in enumerate(session.recipes):
        if recipe_entry['status'] == 'ready':
            try:
                # Use the recipe_action logic
                recipe_data = recipe_entry.get('ai_result')
                if not recipe_data:
                    continue
                
                recipe_name = recipe_data.get('recipe_name', recipe_entry['title'])
                country = recipe_data.get('origin_country', recipe_entry['origin_country'])
                slug = generate_slug(recipe_name, country)
                
                # Check/modify slug
                existing = await db.recipes.find_one({"slug": slug})
                if existing:
                    counter = 1
                    while await db.recipes.find_one({"slug": f"{slug}-{counter}"}):
                        counter += 1
                    slug = f"{slug}-{counter}"
                
                final_recipe = {
                    **recipe_data,
                    "slug": slug,
                    "continent": get_continent(country),
                    "content_language": session.document_language,
                    "status": "published",
                    "date_fetched": datetime.now(timezone.utc).isoformat(),
                    "gpt_used": "Sous-Chef Linguine (Document Import)",
                    "collection_method": "document_import",
                    "source_document": session.document_url,
                    "views_count": 0,
                    "favorites_count": 0,
                    "average_rating": 0,
                    "ratings_count": 0,
                    "comments_count": 0
                }
                
                await db.recipes.insert_one(final_recipe)
                
                recipe_entry['status'] = 'saved'
                recipe_entry['saved_slug'] = slug
                session.saved_count += 1
                saved.append({"index": i, "slug": slug, "name": recipe_name})
                
            except Exception as e:
                recipe_entry['status'] = 'error'
                recipe_entry['error_message'] = str(e)
                errors.append({"index": i, "error": str(e)})
    
    session.status = 'completed'
    session.updated_at = datetime.now(timezone.utc).isoformat()
    
    await db.import_sessions.update_one(
        {"session_id": session_id},
        {"$set": session.to_dict()}
    )
    
    return {
        "success": True,
        "saved": saved,
        "errors": errors,
        "session": session.to_dict()
    }


@document_router.delete("/session/{session_id}")
async def delete_session(session_id: str, authorized: bool = Depends(verify_admin_token)):
    """Delete an import session."""
    result = await db.import_sessions.delete_one({"session_id": session_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True, "message": "Session deleted"}


@document_router.get("/sessions")
async def list_sessions(authorized: bool = Depends(verify_admin_token)):
    """List all import sessions."""
    sessions = await db.import_sessions.find(
        {},
        {"_id": 0, "recipes.raw_text": 0, "recipes.ai_result": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {"sessions": sessions}
