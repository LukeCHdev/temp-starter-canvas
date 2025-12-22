#!/usr/bin/env python3
"""Translation Worker - Continuous Background Process

This worker:
1. Polls the translation_queue collection every 5 seconds
2. Processes pending translation jobs
3. Updates recipe translations in the database
4. Handles failures with retry logic

Run: python translation_worker.py
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from services.content_translation_service import content_translation_service, SUPPORTED_LANGUAGES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
POLL_INTERVAL = 5  # seconds
MAX_RETRIES = 3
BATCH_SIZE = 5  # Process up to 5 jobs per cycle


class TranslationWorker:
    """Background worker for processing translation jobs."""
    
    def __init__(self):
        self.mongo_url = os.environ.get('MONGO_URL')
        self.db_name = os.environ.get('DB_NAME')
        self.client = None
        self.db = None
        self.running = False
    
    async def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        logger.info(f"Connected to MongoDB: {self.db_name}")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def process_job(self, job: dict) -> bool:
        """Process a single translation job.
        
        Returns True if successful, False otherwise.
        """
        recipe_id = job.get('recipe_id')
        target_lang = job.get('target_lang')
        job_id = job.get('_id')
        
        logger.info(f"Processing translation job: {recipe_id} -> {target_lang}")
        
        try:
            # Get the recipe
            recipe = await self.db.recipes.find_one(
                {'id': recipe_id},
                {'_id': 0}
            )
            
            if not recipe:
                # Try by slug
                recipe = await self.db.recipes.find_one(
                    {'slug': recipe_id},
                    {'_id': 0}
                )
            
            if not recipe:
                logger.error(f"Recipe not found: {recipe_id}")
                await self._mark_job_failed(job_id, "Recipe not found")
                return False
            
            # Check if source language matches target (no translation needed)
            content_lang = recipe.get('content_language', 'en')[:2].lower()
            if content_lang == target_lang:
                # Copy canonical content as "translation"
                translated_content = {
                    'recipe_name': recipe.get('recipe_name', ''),
                    'history_summary': recipe.get('history_summary', ''),
                    'characteristic_profile': recipe.get('characteristic_profile', ''),
                    'no_no_rules': recipe.get('no_no_rules', []),
                    'special_techniques': recipe.get('special_techniques', []),
                    'instructions': recipe.get('instructions', []),
                    'ingredients': recipe.get('ingredients', []),
                    'wine_pairing': recipe.get('wine_pairing', {})
                }
            else:
                # Translate the content
                translated_content = await content_translation_service.translate_recipe_content(
                    recipe, target_lang
                )
            
            # Store translation in recipe document
            translation_data = {
                'status': 'ready',
                'translated_at': datetime.now(timezone.utc).isoformat(),
                **translated_content
            }
            
            # Update recipe with translation
            await self.db.recipes.update_one(
                {'slug': recipe.get('slug')},
                {
                    '$set': {
                        f'translations.{target_lang}': translation_data
                    }
                }
            )
            
            # Mark job as completed
            await self.db.translation_queue.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'completed',
                        'completed_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Successfully translated {recipe_id} to {target_lang}")
            return True
            
        except Exception as e:
            logger.error(f"Translation failed for {recipe_id}: {str(e)}")
            await self._mark_job_failed(job_id, str(e))
            return False
    
    async def _mark_job_failed(self, job_id, error_message: str):
        """Mark a job as failed and update retry count."""
        job = await self.db.translation_queue.find_one({'_id': job_id})
        retry_count = job.get('retry_count', 0) + 1
        
        if retry_count >= MAX_RETRIES:
            # Permanent failure
            await self.db.translation_queue.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'failed',
                        'error': error_message,
                        'failed_at': datetime.now(timezone.utc).isoformat(),
                        'retry_count': retry_count
                    }
                }
            )
            
            # Also update recipe translation status to failed
            recipe_id = job.get('recipe_id')
            target_lang = job.get('target_lang')
            
            await self.db.recipes.update_one(
                {'$or': [{'id': recipe_id}, {'slug': recipe_id}]},
                {
                    '$set': {
                        f'translations.{target_lang}': {
                            'status': 'failed',
                            'failed_at': datetime.now(timezone.utc).isoformat(),
                            'retry_count': retry_count
                        }
                    }
                }
            )
            logger.warning(f"Job {job_id} permanently failed after {MAX_RETRIES} retries")
        else:
            # Retry later
            await self.db.translation_queue.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'pending',
                        'last_error': error_message,
                        'retry_count': retry_count
                    }
                }
            )
            logger.info(f"Job {job_id} will be retried (attempt {retry_count}/{MAX_RETRIES})")
    
    async def poll_and_process(self):
        """Poll for pending jobs and process them."""
        # Find pending jobs
        cursor = self.db.translation_queue.find(
            {'status': 'pending'}
        ).sort('queued_at', 1).limit(BATCH_SIZE)
        
        jobs = await cursor.to_list(length=BATCH_SIZE)
        
        if jobs:
            logger.info(f"Found {len(jobs)} pending translation jobs")
            
            for job in jobs:
                # Mark as processing
                await self.db.translation_queue.update_one(
                    {'_id': job['_id']},
                    {'$set': {'status': 'processing', 'started_at': datetime.now(timezone.utc).isoformat()}}
                )
                
                # Process the job
                await self.process_job(job)
                
                # Small delay between jobs to avoid rate limits
                await asyncio.sleep(1)
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info("Translation worker started")
        
        await self.connect()
        
        try:
            while self.running:
                try:
                    await self.poll_and_process()
                except Exception as e:
                    logger.error(f"Error in worker loop: {str(e)}")
                
                # Wait before next poll
                await asyncio.sleep(POLL_INTERVAL)
        finally:
            await self.disconnect()
            logger.info("Translation worker stopped")
    
    def stop(self):
        """Stop the worker."""
        self.running = False


async def main():
    worker = TranslationWorker()
    
    # Handle graceful shutdown
    import signal
    
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        worker.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await worker.run()


if __name__ == '__main__':
    asyncio.run(main())
