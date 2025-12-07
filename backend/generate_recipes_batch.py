# Batch Recipe Generation Script - 3 recipes per country (30 total)

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging
import json
from datetime import datetime, timezone
from services.recipe_generator import recipe_generator
from services.authenticity_engine import authenticity_engine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Countries and their regions
COUNTRIES = [
    {"name": "Italy", "region": "Mediterranean"},
    {"name": "Sweden", "region": "Nordic"},
    {"name": "Japan", "region": "East Asia"},
    {"name": "Mexico", "region": "Latin America"},
    {"name": "Greece", "region": "Mediterranean"},
    {"name": "South Korea", "region": "East Asia"},
    {"name": "France", "region": "Mediterranean"},
    {"name": "Thailand", "region": "Southeast Asia"},
    {"name": "India", "region": "South Asia"},
    {"name": "Spain", "region": "Mediterranean"}
]

# 3 recipes per country for this batch
RECIPES_BATCH = {
    "Italy": ["Carbonara", "Cacio e Pepe", "Amatriciana"],
    "Sweden": ["Köttbullar", "Gravlax", "Janssons Frestelse"],
    "Japan": ["Ramen", "Sushi", "Tempura"],
    "Mexico": ["Tacos al Pastor", "Mole Poblano", "Pozole"],
    "Greece": ["Moussaka", "Souvlaki", "Tzatziki"],
    "South Korea": ["Kimchi", "Bibimbap", "Bulgogi"],
    "France": ["Coq au Vin", "Bouillabaisse", "Ratatouille"],
    "Thailand": ["Pad Thai", "Tom Yum Goong", "Green Curry"],
    "India": ["Butter Chicken", "Biryani", "Tandoori Chicken"],
    "Spain": ["Paella", "Gazpacho", "Tortilla Española"]
}

# Generation statistics
stats = {
    "total_attempted": 0,
    "total_succeeded": 0,
    "total_failed": 0,
    "total_rejected": 0,
    "countries": {},
    "errors": {},
    "start_time": None,
    "end_time": None
}

async def generate_country_batch(db, country: str, region: str, recipes: list):
    """Generate recipes for a single country."""
    country_stats = {
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "rejected": 0,
        "errors": []
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🇮🇹 COUNTRY: {country} ({region})")
    logger.info(f"📝 BATCH SIZE: {len(recipes)} recipes")
    logger.info(f"{'='*60}\n")
    
    for dish_name in recipes:
        country_stats["attempted"] += 1
        stats["total_attempted"] += 1
        
        try:
            logger.info(f"🍳 Generating: {dish_name}...")
            
            # Generate recipe with retry logic
            recipe_data = await recipe_generator.generate_recipe(
                dish_name=dish_name,
                country=country,
                region=region
            )
            
            # Validate authenticity
            is_valid, rejection_reason, validation_report = authenticity_engine.validate_recipe(recipe_data)
            
            if not is_valid:
                recipe_data['status'] = 'rejected'
                recipe_data['rejection_reason'] = rejection_reason
                await db.recipes.insert_one(recipe_data)
                
                country_stats["rejected"] += 1
                stats["total_rejected"] += 1
                
                logger.warning(f"  ⚠️  REJECTED: {rejection_reason}")
                logger.warning(f"  Validation report: {json.dumps(validation_report, indent=2)}")
            else:
                recipe_data['status'] = 'published'
                await db.recipes.insert_one(recipe_data)
                
                country_stats["succeeded"] += 1
                stats["total_succeeded"] += 1
                
                logger.info(f"  ✅ SUCCESS: {dish_name} (slug: {recipe_data['slug']})")
                logger.info(f"  Authenticity rank: {recipe_data.get('source_validation', {}).get('authenticity_rank', 'N/A')}")
            
            # Small delay between recipes
            await asyncio.sleep(2)
            
        except Exception as e:
            country_stats["failed"] += 1
            stats["total_failed"] += 1
            
            error_type = type(e).__name__
            error_msg = str(e)
            
            country_stats["errors"].append({
                "dish": dish_name,
                "error_type": error_type,
                "error_message": error_msg,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Track error types globally
            if error_type not in stats["errors"]:
                stats["errors"][error_type] = 0
            stats["errors"][error_type] += 1
            
            logger.error(f"  ❌ ERROR: {dish_name}")
            logger.error(f"  Exception: {error_type}: {error_msg}")
    
    stats["countries"][country] = country_stats
    
    logger.info(f"\n📊 {country} Summary:")
    logger.info(f"  Attempted: {country_stats['attempted']}")
    logger.info(f"  Succeeded: {country_stats['succeeded']}")
    logger.info(f"  Rejected:  {country_stats['rejected']}")
    logger.info(f"  Failed:    {country_stats['failed']}")
    
    return country_stats

async def generate_batch():
    """Generate 3 recipes per country (30 total)."""
    stats["start_time"] = datetime.now(timezone.utc).isoformat()
    
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        logger.info("\n" + "="*60)
        logger.info("🚀 STARTING BATCH RECIPE GENERATION")
        logger.info("📦 Batch size: 3 recipes per country")
        logger.info(f"🌍 Countries: {len(COUNTRIES)}")
        logger.info(f"📝 Total target: {len(COUNTRIES) * 3} recipes")
        logger.info("="*60 + "\n")
        
        for country_info in COUNTRIES:
            country = country_info["name"]
            region = country_info["region"]
            recipes = RECIPES_BATCH.get(country, [])
            
            await generate_country_batch(db, country, region, recipes)
        
        stats["end_time"] = datetime.now(timezone.utc).isoformat()
        
        # Generate final report
        generate_report()
        
    except Exception as e:
        logger.error(f"💥 FATAL ERROR: {str(e)}")
        raise
    finally:
        client.close()

def generate_report():
    """Generate comprehensive generation report."""
    logger.info("\n" + "="*60)
    logger.info("📊 BATCH GENERATION REPORT")
    logger.info("="*60 + "\n")
    
    logger.info(f"⏱️  Duration: {stats['start_time']} → {stats['end_time']}\n")
    
    logger.info("📈 OVERALL STATISTICS:")
    logger.info(f"  Total Attempted: {stats['total_attempted']}")
    logger.info(f"  ✅ Succeeded:    {stats['total_succeeded']} ({stats['total_succeeded']/stats['total_attempted']*100:.1f}%)")
    logger.info(f"  ⚠️  Rejected:     {stats['total_rejected']} ({stats['total_rejected']/stats['total_attempted']*100:.1f}%)")
    logger.info(f"  ❌ Failed:       {stats['total_failed']} ({stats['total_failed']/stats['total_attempted']*100:.1f}%)")
    
    logger.info("\n🌍 PER-COUNTRY BREAKDOWN:")
    for country, country_stats in stats["countries"].items():
        success_rate = country_stats['succeeded'] / country_stats['attempted'] * 100 if country_stats['attempted'] > 0 else 0
        logger.info(f"\n  {country}:")
        logger.info(f"    Success: {country_stats['succeeded']}/{country_stats['attempted']} ({success_rate:.1f}%)")
        logger.info(f"    Rejected: {country_stats['rejected']}")
        logger.info(f"    Failed: {country_stats['failed']}")
        
        if country_stats['errors']:
            logger.info(f"    Errors:")
            for error in country_stats['errors']:
                logger.info(f"      - {error['dish']}: {error['error_type']}")
    
    if stats["errors"]:
        logger.info("\n🚨 ERROR TYPE DISTRIBUTION:")
        for error_type, count in stats["errors"].items():
            logger.info(f"  {error_type}: {count}")
    
    logger.info("\n🎯 RECOMMENDATIONS:")
    if stats['total_failed'] > stats['total_succeeded']:
        logger.info("  ⚠️  High failure rate detected!")
        logger.info("  → Check Emergent LLM service status")
        logger.info("  → Review retry logic configuration")
        logger.info("  → Consider increasing delay between requests")
    elif stats['total_rejected'] > stats['total_succeeded']:
        logger.info("  ⚠️  High rejection rate detected!")
        logger.info("  → Review authenticity validation rules")
        logger.info("  → Check AI prompt quality")
    else:
        logger.info("  ✅ Generation successful!")
        logger.info("  → Ready to proceed to full 10-recipe batch")
    
    logger.info("\n" + "="*60 + "\n")
    
    # Save report to file
    report_path = f"/tmp/recipe_generation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"📄 Full report saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(generate_batch())
