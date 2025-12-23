"""
Search API Routes
Language-aware search endpoints with translation memory integration.
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

search_router = APIRouter(prefix="/api/search", tags=["search"])

# Database reference (set by main server)
_db = None
_search_service = None
_tm_service = None

def set_search_db(database):
    """Set the database reference for search services."""
    global _db, _search_service, _tm_service
    _db = database
    
    from services.language_search_service import get_search_service
    from services.translation_memory_service import get_translation_memory
    
    _search_service = get_search_service(database)
    _tm_service = get_translation_memory(database)


@search_router.get("/recipes")
async def search_recipes(
    q: str = Query(..., min_length=1, description="Search query"),
    lang: str = Query("en", description="Target language for results"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    fuzzy: bool = Query(True, description="Enable fuzzy matching")
):
    """
    Search recipes with language awareness.
    
    Features:
    - Searches in both original and translated content
    - Language-specific text processing (stop words, normalization)
    - Fuzzy matching for similar queries
    - Results scored by relevance and language match
    """
    if not _search_service:
        return {"error": "Search service not initialized", "recipes": []}
    
    try:
        result = await _search_service.search(
            query=q,
            lang=lang,
            limit=limit,
            include_translations=True
        )
        
        # Log search for analytics
        await _db.search_analytics.insert_one({
            "query": q,
            "lang": lang,
            "results_count": len(result.get("recipes", [])),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": str(e), "recipes": [], "metadata": {"query": q, "lang": lang}}


@search_router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial query"),
    lang: str = Query("en", description="Language for suggestions"),
    limit: int = Query(5, ge=1, le=10)
):
    """
    Get search suggestions based on partial query.
    Returns recipe names that match the query prefix.
    """
    if not _db:
        return {"suggestions": []}
    
    try:
        # Search in recipe names
        cursor = _db.recipes.find(
            {
                "recipe_name": {"$regex": f"^{q}", "$options": "i"},
                "status": "published"
            },
            {"_id": 0, "recipe_name": 1, "slug": 1, "origin_country": 1}
        ).limit(limit)
        
        recipes = await cursor.to_list(limit)
        
        suggestions = [
            {
                "text": r["recipe_name"],
                "slug": r["slug"],
                "country": r.get("origin_country", "")
            }
            for r in recipes
        ]
        
        return {"suggestions": suggestions, "query": q}
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return {"suggestions": [], "query": q}


# Translation Memory endpoints
@search_router.get("/tm/lookup")
async def tm_lookup(
    text: str = Query(..., description="Text to find translation for"),
    source_lang: str = Query("en", description="Source language"),
    target_lang: str = Query(..., description="Target language"),
    fuzzy: bool = Query(True, description="Enable fuzzy matching")
):
    """
    Look up translation in translation memory.
    Returns exact match or fuzzy match if enabled.
    """
    if not _tm_service:
        return {"error": "Translation memory not initialized"}
    
    try:
        result = await _tm_service.lookup(text, source_lang, target_lang, fuzzy)
        return {
            "found": result is not None,
            "source_text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "result": result
        }
    except Exception as e:
        logger.error(f"TM lookup error: {e}")
        return {"error": str(e), "found": False}


@search_router.post("/tm/store")
async def tm_store(
    source_text: str,
    translated_text: str,
    source_lang: str = "en",
    target_lang: str = "it",
    confidence: float = 1.0,
    verified: bool = False,
    context: Optional[str] = None,
    source_type: str = "ai"
):
    """
    Store a translation in translation memory.
    """
    if not _tm_service:
        return {"error": "Translation memory not initialized"}
    
    try:
        result = await _tm_service.store(
            source_text=source_text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=confidence,
            verified=verified,
            context=context,
            source_type=source_type
        )
        return result
    except Exception as e:
        logger.error(f"TM store error: {e}")
        return {"error": str(e), "success": False}


@search_router.get("/tm/stats")
async def tm_stats():
    """
    Get translation memory statistics.
    """
    if not _tm_service:
        return {"error": "Translation memory not initialized"}
    
    try:
        stats = await _tm_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"TM stats error: {e}")
        return {"error": str(e)}


@search_router.post("/tm/batch-lookup")
async def tm_batch_lookup(
    texts: list,
    source_lang: str = "en",
    target_lang: str = "it",
    fuzzy: bool = True
):
    """
    Look up multiple translations at once.
    """
    if not _tm_service:
        return {"error": "Translation memory not initialized"}
    
    try:
        results = await _tm_service.batch_lookup(texts, source_lang, target_lang, fuzzy)
        
        found_count = sum(1 for v in results.values() if v is not None)
        
        return {
            "total": len(texts),
            "found": found_count,
            "not_found": len(texts) - found_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"TM batch lookup error: {e}")
        return {"error": str(e)}
