"""Auto-Translation Service - Ensures all new recipes are automatically translated.

This service:
1. Queues translations for all supported languages when a recipe is created
2. Ensures consistent multilingual coverage across the platform
3. Works with the translation_worker.py background process

Usage:
    from services.auto_translation_service import auto_translate_recipe
    await auto_translate_recipe(recipe_slug)
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

# Supported languages for translation
SUPPORTED_LANGUAGES = ['en', 'es', 'it', 'fr', 'de']
TARGET_LANGUAGES = ['es', 'it', 'fr', 'de']  # Languages to auto-translate to (excluding source 'en')


class AutoTranslationService:
    """Service for automatically queueing translations for new recipes."""
    
    def __init__(self):
        self.db = None
    
    def set_database(self, database):
        """Set the database connection."""
        self.db = database
    
    async def queue_translation(self, recipe_slug: str, target_lang: str) -> bool:
        """Queue a single translation job.
        
        Args:
            recipe_slug: The recipe's slug identifier
            target_lang: Target language code (es, it, fr, de)
            
        Returns:
            bool: True if job was queued, False if already exists
        """
        if not self.db:
            logger.error("Database not set for AutoTranslationService")
            return False
            
        if target_lang not in TARGET_LANGUAGES:
            logger.warning(f"Unsupported target language: {target_lang}")
            return False
        
        # Check if job already exists (pending or processing)
        existing = await self.db.translation_queue.find_one({
            'recipe_id': recipe_slug,
            'target_lang': target_lang,
            'status': {'$in': ['pending', 'processing']}
        })
        
        if existing:
            logger.info(f"Translation job already queued: {recipe_slug} -> {target_lang}")
            return False
        
        # Check if translation is already ready
        recipe = await self.db.recipes.find_one({'slug': recipe_slug})
        if recipe:
            existing_trans = recipe.get('translations', {}).get(target_lang, {})
            if existing_trans.get('status') == 'ready':
                logger.info(f"Translation already ready: {recipe_slug} -> {target_lang}")
                return False
        
        # Queue the job
        job = {
            'recipe_id': recipe_slug,
            'target_lang': target_lang,
            'status': 'pending',
            'queued_at': datetime.now(timezone.utc).isoformat(),
            'retry_count': 0,
            'auto_queued': True  # Mark as auto-queued for tracking
        }
        
        await self.db.translation_queue.insert_one(job)
        logger.info(f"Auto-queued translation: {recipe_slug} -> {target_lang}")
        return True
    
    async def auto_translate_recipe(self, recipe_slug: str, source_lang: str = 'en') -> dict:
        """Automatically queue translations for a recipe in all supported languages.
        
        This is the main entry point called when a new recipe is created.
        
        Args:
            recipe_slug: The recipe's slug identifier
            source_lang: Source language code (default: 'en')
            
        Returns:
            dict: Summary of queued translations
        """
        if not self.db:
            logger.error("Database not set for AutoTranslationService")
            return {'success': False, 'error': 'Database not configured'}
        
        queued = []
        skipped = []
        
        for lang in TARGET_LANGUAGES:
            # Skip if target is same as source
            if lang == source_lang:
                skipped.append(lang)
                continue
            
            success = await self.queue_translation(recipe_slug, lang)
            if success:
                queued.append(lang)
            else:
                skipped.append(lang)
        
        logger.info(f"Auto-translation for {recipe_slug}: queued={queued}, skipped={skipped}")
        
        return {
            'success': True,
            'recipe_slug': recipe_slug,
            'source_lang': source_lang,
            'queued_languages': queued,
            'skipped_languages': skipped,
            'message': f"Queued {len(queued)} translations for {recipe_slug}"
        }
    
    async def ensure_all_recipes_have_translations(self, limit: int = 100) -> dict:
        """Check all recipes and queue missing translations.
        
        Useful for backfilling translations for existing recipes.
        
        Args:
            limit: Maximum number of recipes to process
            
        Returns:
            dict: Summary of processing results
        """
        if not self.db:
            return {'success': False, 'error': 'Database not configured'}
        
        recipes = await self.db.recipes.find(
            {'status': 'published'},
            {'slug': 1, 'translations': 1}
        ).limit(limit).to_list(limit)
        
        total_queued = 0
        recipes_processed = 0
        
        for recipe in recipes:
            slug = recipe.get('slug')
            if not slug:
                continue
                
            recipes_processed += 1
            translations = recipe.get('translations', {})
            
            for lang in TARGET_LANGUAGES:
                lang_trans = translations.get(lang, {})
                # Queue if not ready and not already pending
                if lang_trans.get('status') != 'ready':
                    success = await self.queue_translation(slug, lang)
                    if success:
                        total_queued += 1
        
        return {
            'success': True,
            'recipes_processed': recipes_processed,
            'translations_queued': total_queued
        }


# Global singleton instance
auto_translation_service = AutoTranslationService()


# Convenience function for direct import
async def auto_translate_recipe(recipe_slug: str, source_lang: str = 'en') -> dict:
    """Queue automatic translations for a recipe.
    
    This function should be called whenever a new recipe is created.
    """
    return await auto_translation_service.auto_translate_recipe(recipe_slug, source_lang)
