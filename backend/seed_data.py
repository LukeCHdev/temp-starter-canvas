# Data seeding script
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initial regions data
REGIONS = [
    {
        "name": "Mediterranean",
        "slug": "mediterranean",
        "description": "Sun-kissed shores where olive groves meet azure waters, birthing cuisines of extraordinary depth and flavor.",
        "countries": ["Italy", "Greece", "Spain", "France", "Turkey"],
        "image_url": "",
        "typical_characteristics": "Olive oil, fresh vegetables, seafood, aromatic herbs",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "name": "East Asia",
        "slug": "east-asia",
        "description": "Ancient culinary traditions where balance, harmony, and respect for ingredients create timeless dishes.",
        "countries": ["Japan", "China", "Korea", "Thailand", "Vietnam"],
        "image_url": "",
        "typical_characteristics": "Rice, soy, fermented ingredients, delicate balance of flavors",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "name": "Latin America",
        "slug": "latin-america",
        "description": "Bold flavors and vibrant colors reflect the passionate spirit of cultures shaped by indigenous and colonial influences.",
        "countries": ["Mexico", "Peru", "Argentina", "Brazil", "Colombia"],
        "image_url": "",
        "typical_characteristics": "Corn, beans, chilies, tropical fruits, rich stews",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

# Initial countries data
COUNTRIES = [
    {
        "name": "Italy",
        "slug": "italy",
        "region": "Mediterranean",
        "country_code": "IT",
        "language": "Italian",
        "domain_extension": ".it",
        "typical_dishes": [],
        "culinary_description": "Italian cuisine is a love letter to simplicity and quality. Each region tells its own story through pasta, olive oil, and generations of tradition.",
        "image_url": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "name": "Japan",
        "slug": "japan",
        "region": "East Asia",
        "country_code": "JP",
        "language": "Japanese",
        "domain_extension": ".jp",
        "typical_dishes": [],
        "culinary_description": "Japanese cooking is meditation made edible. Precision, seasonality, and profound respect for ingredients create dishes of ethereal beauty.",
        "image_url": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "name": "Mexico",
        "slug": "mexico",
        "region": "Latin America",
        "country_code": "MX",
        "language": "Spanish",
        "domain_extension": ".mx",
        "typical_dishes": [],
        "culinary_description": "Mexican cuisine dances between ancient indigenous wisdom and centuries of cultural fusion, creating explosions of flavor in every bite.",
        "image_url": "",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

async def seed_database():
    """Seed initial data."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Clear existing data
        await db.regions.delete_many({})
        await db.countries.delete_many({})
        logger.info("Cleared existing data")
        
        # Insert regions
        if REGIONS:
            await db.regions.insert_many(REGIONS)
            logger.info(f"Inserted {len(REGIONS)} regions")
        
        # Insert countries
        if COUNTRIES:
            await db.countries.insert_many(COUNTRIES)
            logger.info(f"Inserted {len(COUNTRIES)} countries")
        
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
