"""
Pre-translate Top Recipes Script
Queues translation jobs for top-rated and high-traffic recipes in all supported languages.
Tracks translation status to avoid duplicates.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported target languages (excluding source language 'en')
TARGET_LANGUAGES = ['it', 'fr', 'es', 'de']

async def get_top_recipes(db, limit: int = 100):
    """
    Get top recipes sorted by:
    1. Average rating (highest first)
    2. Ratings count (most reviewed first)
    3. Date fetched (newest first)
    """
    recipes = await db.recipes.find(
        {"status": "published"},
        {"_id": 0, "slug": 1, "recipe_name": 1, "average_rating": 1, "ratings_count": 1, "date_fetched": 1}
    ).sort([
        ("average_rating", -1),
        ("ratings_count", -1),
        ("date_fetched", -1)
    ]).to_list(limit)
    
    return recipes


async def get_translation_status(db, recipe_slug: str, target_lang: str):
    """Check if translation already exists or is queued."""
    # Check translations collection
    existing = await db.translations.find_one({
        "slug": recipe_slug,
        "lang": target_lang
    })
    
    if existing:
        return existing.get('status', 'unknown')
    
    # Check translation queue
    queued = await db.translation_queue.find_one({
        "recipe_slug": recipe_slug,
        "target_lang": target_lang,
        "status": {"$in": ["pending", "processing"]}
    })
    
    if queued:
        return "queued"
    
    return None


async def queue_translation(db, recipe_slug: str, target_lang: str):
    """Add a translation job to the queue."""
    now = datetime.now(timezone.utc).isoformat()
    
    await db.translation_queue.update_one(
        {
            "recipe_slug": recipe_slug,
            "target_lang": target_lang
        },
        {
            "$set": {
                "status": "pending",
                "queued_at": now,
                "priority": "batch",
                "source": "pre_translation_script"
            },
            "$setOnInsert": {
                "recipe_slug": recipe_slug,
                "target_lang": target_lang,
                "created_at": now
            }
        },
        upsert=True
    )


async def pretranslate_top_recipes(limit: int = 100):
    """
    Main function to queue translations for top recipes.
    
    Args:
        limit: Number of top recipes to pre-translate
    """
    # Connect to database
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'sous_chef_linguine')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    logger.info(f"Starting pre-translation for top {limit} recipes...")
    
    # Get top recipes
    recipes = await get_top_recipes(db, limit)
    logger.info(f"Found {len(recipes)} recipes to process")
    
    stats = {
        "total_recipes": len(recipes),
        "translations_queued": 0,
        "already_translated": 0,
        "already_queued": 0,
        "errors": 0
    }
    
    for idx, recipe in enumerate(recipes):
        slug = recipe.get('slug')
        name = recipe.get('recipe_name', slug)
        
        logger.info(f"[{idx + 1}/{len(recipes)}] Processing: {name}")
        
        for lang in TARGET_LANGUAGES:
            try:
                status = await get_translation_status(db, slug, lang)
                
                if status == 'ready':
                    stats["already_translated"] += 1
                    logger.debug(f"  {lang}: Already translated")
                elif status == 'queued' or status == 'pending' or status == 'processing':
                    stats["already_queued"] += 1
                    logger.debug(f"  {lang}: Already in queue")
                else:
                    # Queue the translation
                    await queue_translation(db, slug, lang)
                    stats["translations_queued"] += 1
                    logger.info(f"  {lang}: Queued for translation")
                    
            except Exception as e:
                stats["errors"] += 1
                logger.error(f"  {lang}: Error - {e}")
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("PRE-TRANSLATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total recipes processed: {stats['total_recipes']}")
    logger.info(f"Languages per recipe: {len(TARGET_LANGUAGES)}")
    logger.info(f"Translations queued: {stats['translations_queued']}")
    logger.info(f"Already translated: {stats['already_translated']}")
    logger.info(f"Already in queue: {stats['already_queued']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 50)
    
    # Close connection
    client.close()
    
    return stats


async def get_translation_queue_status(db):
    """Get current translation queue statistics."""
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.translation_queue.aggregate(pipeline).to_list(10)
    return {r['_id']: r['count'] for r in results}


if __name__ == "__main__":
    asyncio.run(pretranslate_top_recipes(100))
