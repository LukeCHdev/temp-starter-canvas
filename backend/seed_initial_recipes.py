# Seed initial 20-30 recipes as specified

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime, timezone
from services.recipe_generator import recipe_generator
from services.authenticity_engine import authenticity_engine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initial recipes as specified by requirements
INITIAL_RECIPES = [
    # Italian
    {"dish": "Carbonara", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Cacio e Pepe", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Amatriciana", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Gricia", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Pasta alla Genovese", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Cotoletta alla Milanese", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Plin Piemontesi", "country": "Italy", "region": "Mediterranean"},
    {"dish": "Risotto alla Milanese", "country": "Italy", "region": "Mediterranean"},
    
    # Swedish
    {"dish": "Gravlax", "country": "Sweden", "region": "Nordic"},
    {"dish": "Köttbullar", "country": "Sweden", "region": "Nordic"},
    {"dish": "Janssons Frestelse", "country": "Sweden", "region": "Nordic"},
    
    # Japanese
    {"dish": "Sushi", "country": "Japan", "region": "East Asia"},
    {"dish": "Ramen", "country": "Japan", "region": "East Asia"},
    {"dish": "Tempura", "country": "Japan", "region": "East Asia"},
    {"dish": "Tonkatsu", "country": "Japan", "region": "East Asia"},
    
    # Mexican
    {"dish": "Tacos al Pastor", "country": "Mexico", "region": "Latin America"},
    {"dish": "Mole Poblano", "country": "Mexico", "region": "Latin America"},
    {"dish": "Pozole", "country": "Mexico", "region": "Latin America"},
    {"dish": "Chiles en Nogada", "country": "Mexico", "region": "Latin America"},
    
    # French
    {"dish": "Coq au Vin", "country": "France", "region": "Mediterranean"},
    {"dish": "Bouillabaisse", "country": "France", "region": "Mediterranean"},
    {"dish": "Ratatouille", "country": "France", "region": "Mediterranean"},
    {"dish": "Quiche Lorraine", "country": "France", "region": "Mediterranean"},
    
    # Spanish
    {"dish": "Paella", "country": "Spain", "region": "Mediterranean"},
    {"dish": "Gazpacho", "country": "Spain", "region": "Mediterranean"},
    {"dish": "Tortilla Española", "country": "Spain", "region": "Mediterranean"},
]

stats = {
    "attempted": 0,
    "succeeded": 0,
    "failed": 0,
    "rejected": 0,
    "errors": []
}

async def seed_initial_recipes():
    """Seed initial 20-30 recipes."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🌟 SEEDING INITIAL RECIPES")
    logger.info(f"📦 Target: {len(INITIAL_RECIPES)} recipes")
    logger.info(f"{'='*60}\n")
    
    try:
        for recipe_info in INITIAL_RECIPES:
            dish = recipe_info["dish"]
            country = recipe_info["country"]
            region = recipe_info["region"]
            
            stats["attempted"] += 1
            
            # Check if already exists
            existing = await db.recipes.find_one({"title_original": dish, "country": country})
            if existing:
                logger.info(f"⏭️  SKIP: {dish} (already exists)")
                continue
            
            try:
                logger.info(f"🍳 Generating: {dish} ({country})")
                
                # Generate recipe
                recipe_data = await recipe_generator.generate_recipe(
                    dish_name=dish,
                    country=country,
                    region=region
                )
                
                # Validate
                is_valid, rejection_reason, validation_report = authenticity_engine.validate_recipe(recipe_data)
                
                if not is_valid:
                    recipe_data['status'] = 'rejected'
                    recipe_data['rejection_reason'] = rejection_reason
                    await db.recipes.insert_one(recipe_data)
                    stats["rejected"] += 1
                    logger.warning(f"  ⚠️  REJECTED: {rejection_reason}")
                else:
                    recipe_data['status'] = 'published'
                    await db.recipes.insert_one(recipe_data)
                    stats["succeeded"] += 1
                    logger.info(f"  ✅ SUCCESS: {recipe_data['slug']}")
                
                # Small delay
                await asyncio.sleep(3)
                
            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append({"dish": dish, "error": str(e)})
                logger.error(f"  ❌ ERROR: {str(e)}")
        
        # Final report
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 SEEDING COMPLETE")
        logger.info(f"  Attempted: {stats['attempted']}")
        logger.info(f"  ✅ Succeeded: {stats['succeeded']}")
        logger.info(f"  ⚠️  Rejected: {stats['rejected']}")
        logger.info(f"  ❌ Failed: {stats['failed']}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_initial_recipes())
