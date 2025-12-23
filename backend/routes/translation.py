"""Translation Routes - Language-aware recipe content endpoints

These endpoints implement the approved architecture:
1. Returns status + content (or status + null)
2. Queues translations asynchronously
3. Never returns mixed-language content
"""

from fastapi import APIRouter, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)

translation_router = APIRouter(prefix="/api/translations", tags=["translations"])

# MongoDB connection (will be set by main app)
db = None

SUPPORTED_LANGUAGES = ['en', 'es', 'it', 'fr', 'de']


def set_database(database):
    """Set the database reference from main app."""
    global db
    db = database


async def get_recipe_with_language(recipe: dict, lang: str) -> dict:
    """Get recipe content in the requested language.
    
    Returns:
        - If lang matches content_language: canonical content with status='ready'
        - If translation exists and ready: translated content with status='ready'
        - If translation pending: status='pending', content=null
        - If translation failed: status='failed', content=null
        - If no translation: queues translation, returns status='pending', content=null
    """
    slug = recipe.get('slug')
    content_lang = recipe.get('content_language', 'en')[:2].lower()
    target_lang = lang[:2].lower() if lang else 'en'
    
    # If requesting canonical language, return canonical content
    if target_lang == content_lang:
        return {
            'slug': slug,
            'lang': target_lang,
            'status': 'ready',
            'content': {
                'recipe_name': recipe.get('recipe_name', ''),
                'history_summary': recipe.get('history_summary', ''),
                'characteristic_profile': recipe.get('characteristic_profile', ''),
                'no_no_rules': recipe.get('no_no_rules', []),
                'special_techniques': recipe.get('special_techniques', []),
                'instructions': recipe.get('instructions', []),
                'ingredients': recipe.get('ingredients', []),
                'wine_pairing': recipe.get('wine_pairing', {})
            },
            # Include non-translatable metadata
            'metadata': {
                'origin_country': recipe.get('origin_country', ''),
                'origin_region': recipe.get('origin_region', ''),
                'authenticity_level': recipe.get('authenticity_level', 3),
                'photos': recipe.get('photos', []),
                'youtube_links': recipe.get('youtube_links', []),
                'average_rating': recipe.get('average_rating', 0),
                'ratings_count': recipe.get('ratings_count', 0)
            }
        }
    
    # Check if translation exists
    translations = recipe.get('translations', {})
    translation = translations.get(target_lang, {})
    
    if translation.get('status') == 'ready':
        # Translation is ready
        return {
            'slug': slug,
            'lang': target_lang,
            'status': 'ready',
            'content': {
                'recipe_name': translation.get('recipe_name', ''),
                'history_summary': translation.get('history_summary', ''),
                'characteristic_profile': translation.get('characteristic_profile', ''),
                'no_no_rules': translation.get('no_no_rules', []),
                'special_techniques': translation.get('special_techniques', []),
                'instructions': translation.get('instructions', []),
                'ingredients': translation.get('ingredients', []),
                'wine_pairing': translation.get('wine_pairing', {})
            },
            'metadata': {
                'origin_country': recipe.get('origin_country', ''),
                'origin_region': recipe.get('origin_region', ''),
                'authenticity_level': recipe.get('authenticity_level', 3),
                'photos': recipe.get('photos', []),
                'youtube_links': recipe.get('youtube_links', []),
                'average_rating': recipe.get('average_rating', 0),
                'ratings_count': recipe.get('ratings_count', 0)
            }
        }
    
    elif translation.get('status') == 'pending':
        # Translation is in progress
        return {
            'slug': slug,
            'lang': target_lang,
            'status': 'pending',
            'content': None,
            'metadata': {
                'origin_country': recipe.get('origin_country', ''),
                'origin_region': recipe.get('origin_region', ''),
                'authenticity_level': recipe.get('authenticity_level', 3),
                'photos': recipe.get('photos', []),
                'average_rating': recipe.get('average_rating', 0),
                'ratings_count': recipe.get('ratings_count', 0)
            }
        }
    
    elif translation.get('status') == 'failed':
        # Translation failed
        return {
            'slug': slug,
            'lang': target_lang,
            'status': 'failed',
            'content': None,
            'metadata': {
                'origin_country': recipe.get('origin_country', ''),
                'origin_region': recipe.get('origin_region', ''),
                'authenticity_level': recipe.get('authenticity_level', 3),
                'photos': recipe.get('photos', []),
                'average_rating': recipe.get('average_rating', 0),
                'ratings_count': recipe.get('ratings_count', 0)
            }
        }
    
    else:
        # No translation exists - queue it
        await queue_translation(slug, target_lang)
        
        # Mark as pending in recipe
        await db.recipes.update_one(
            {'slug': slug},
            {
                '$set': {
                    f'translations.{target_lang}': {
                        'status': 'pending',
                        'queued_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            }
        )
        
        return {
            'slug': slug,
            'lang': target_lang,
            'status': 'pending',
            'content': None,
            'metadata': {
                'origin_country': recipe.get('origin_country', ''),
                'origin_region': recipe.get('origin_region', ''),
                'authenticity_level': recipe.get('authenticity_level', 3),
                'photos': recipe.get('photos', []),
                'average_rating': recipe.get('average_rating', 0),
                'ratings_count': recipe.get('ratings_count', 0)
            }
        }


async def queue_translation(recipe_id: str, target_lang: str):
    """Add a translation job to the queue."""
    # Check if job already exists
    existing = await db.translation_queue.find_one({
        'recipe_id': recipe_id,
        'target_lang': target_lang,
        'status': {'$in': ['pending', 'processing']}
    })
    
    if existing:
        logger.info(f"Translation job already queued: {recipe_id} -> {target_lang}")
        return
    
    job = {
        'recipe_id': recipe_id,
        'target_lang': target_lang,
        'status': 'pending',
        'queued_at': datetime.now(timezone.utc).isoformat(),
        'retry_count': 0
    }
    
    await db.translation_queue.insert_one(job)
    logger.info(f"Queued translation: {recipe_id} -> {target_lang}")


@translation_router.get("/recipe/{slug}")
async def get_recipe_translated(
    slug: str,
    lang: str = Query("en", description="Target language code")
):
    """Get a single recipe with content in the requested language.
    
    Returns:
        - status: 'ready' | 'pending' | 'failed'
        - content: translated content (or null if not ready)
        - metadata: non-translatable recipe data
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}. Supported: {SUPPORTED_LANGUAGES}")
    
    recipe = await db.recipes.find_one(
        {'slug': slug, 'status': 'published'},
        {'_id': 0}
    )
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    return await get_recipe_with_language(recipe, lang)


@translation_router.get("/recipes")
async def get_recipes_translated(
    lang: str = Query("en", description="Target language code"),
    country: Optional[str] = None,
    continent: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1)
):
    """Get recipes with content in the requested language.
    
    Each recipe will have:
        - status: 'ready' | 'pending' | 'failed'
        - content: translated content (or null if not ready)
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    
    # Build query
    query = {'status': 'published'}
    if country:
        query['origin_country'] = {'$regex': f'^{country}$', '$options': 'i'}
    if continent:
        query['continent'] = continent.replace('-', ' ').title()
    
    skip = (page - 1) * limit
    
    # Get recipes
    recipes = await db.recipes.find(query, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.recipes.count_documents(query)
    
    # Process each recipe for language
    results = []
    for recipe in recipes:
        result = await get_recipe_with_language(recipe, lang)
        results.append(result)
    
    return {
        'recipes': results,
        'total': total,
        'page': page,
        'limit': limit,
        'lang': lang
    }


@translation_router.post("/queue")
async def queue_translations(
    slugs: List[str],
    lang: str = Query(..., description="Target language code")
):
    """Queue multiple recipes for translation."""
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    
    queued = 0
    for slug in slugs:
        await queue_translation(slug, lang)
        queued += 1
    
    return {
        'message': f'Queued {queued} translations for {lang}',
        'queued': queued,
        'lang': lang
    }


@translation_router.get("/queue/status")
async def get_queue_status():
    """Get translation queue statistics."""
    pending = await db.translation_queue.count_documents({'status': 'pending'})
    processing = await db.translation_queue.count_documents({'status': 'processing'})
    completed = await db.translation_queue.count_documents({'status': 'completed'})
    failed = await db.translation_queue.count_documents({'status': 'failed'})
    
    return {
        'pending': pending,
        'processing': processing,
        'completed': completed,
        'failed': failed,
        'total': pending + processing + completed + failed
    }


@translation_router.post("/queue/pretranslate-top")
async def pretranslate_top_recipes(limit: int = 100):
    """
    Queue translations for top-rated recipes.
    
    Args:
        limit: Number of top recipes to pre-translate (default: 100)
    
    This endpoint:
    1. Gets top recipes by rating/reviews
    2. Queues translation jobs for IT, FR, ES, DE
    3. Skips already translated recipes
    """
    TARGET_LANGUAGES = ['it', 'fr', 'es', 'de']
    
    # Get top recipes
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0, "slug": 1, "recipe_name": 1, "average_rating": 1, "ratings_count": 1}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1)
    ]).to_list(limit)
    
    stats = {
        "total_recipes": len(recipes),
        "translations_queued": 0,
        "already_exists": 0,
        "errors": 0
    }
    
    for recipe in recipes:
        slug = recipe.get('slug')
        if not slug:
            continue
        
        for lang in TARGET_LANGUAGES:
            try:
                # Check if translation exists
                existing = await db.translations.find_one({
                    "slug": slug,
                    "lang": lang
                })
                
                if existing and existing.get('status') == 'ready':
                    stats["already_exists"] += 1
                    continue
                
                # Check if already queued
                queued = await db.translation_queue.find_one({
                    "recipe_slug": slug,
                    "target_lang": lang,
                    "status": {"$in": ["pending", "processing"]}
                })
                
                if queued:
                    stats["already_exists"] += 1
                    continue
                
                # Queue the translation
                now = datetime.now(timezone.utc).isoformat()
                await db.translation_queue.update_one(
                    {"recipe_slug": slug, "target_lang": lang},
                    {
                        "$set": {
                            "status": "pending",
                            "queued_at": now,
                            "priority": "batch"
                        },
                        "$setOnInsert": {
                            "recipe_slug": slug,
                            "target_lang": lang,
                            "created_at": now
                        }
                    },
                    upsert=True
                )
                stats["translations_queued"] += 1
                
            except Exception:
                stats["errors"] += 1
    
    return {
        "message": f"Pre-translation queued for top {limit} recipes",
        "stats": stats,
        "languages": TARGET_LANGUAGES
    }


@translation_router.get("/queue/coverage")
async def get_translation_coverage():
    """
    Get translation coverage statistics.
    Shows how many recipes are translated per language.
    """
    languages = ['en', 'it', 'fr', 'es', 'de']
    
    # Total published recipes
    total_recipes = await db.recipes.count_documents({"status": "published"})
    
    coverage = {}
    for lang in languages:
        if lang == 'en':
            # English is the source language
            coverage[lang] = {
                "translated": total_recipes,
                "pending": 0,
                "coverage_percent": 100.0
            }
        else:
            # Count translated recipes
            translated = await db.translations.count_documents({
                "lang": lang,
                "status": "ready"
            })
            
            pending = await db.translation_queue.count_documents({
                "target_lang": lang,
                "status": {"$in": ["pending", "processing"]}
            })
            
            coverage[lang] = {
                "translated": translated,
                "pending": pending,
                "coverage_percent": round((translated / total_recipes * 100) if total_recipes > 0 else 0, 1)
            }
    
    return {
        "total_recipes": total_recipes,
        "coverage_by_language": coverage
    }

