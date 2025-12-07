# Script to generate 10 authentic recipes per country

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import logging
from services.recipe_generator import recipe_generator
from services.authenticity_engine import authenticity_engine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

# 10 recipes per country
RECIPES_PER_COUNTRY = {
    "Italy": ["Carbonara", "Cacio e Pepe", "Amatriciana", "Risotto alla Milanese", "Osso Buco", 
              "Tiramisu", "Panna Cotta", "Lasagne alla Bolognese", "Pizza Margherita", "Arancini"],
    
    "Sweden": ["Köttbullar", "Gravlax", "Janssons Frestelse", "Raggmunk", "Smörgåstårta", 
               "Ärtsoppa", "Kroppkakor", "Semla", "Kanelbulle", "Prinsesstårta"],
    
    "Japan": ["Ramen", "Sushi", "Tempura", "Tonkatsu", "Okonomiyaki",
              "Yakitori", "Miso Soup", "Udon", "Takoyaki", "Donburi"],
    
    "Mexico": ["Tacos al Pastor", "Mole Poblano", "Pozole", "Chiles en Nogada", "Tamales",
               "Enchiladas", "Cochinita Pibil", "Tostadas", "Sopes", "Elote"],
    
    "Greece": ["Moussaka", "Souvlaki", "Tzatziki", "Spanakopita", "Dolmades",
               "Greek Salad", "Pastitsio", "Fasolada", "Baklava", "Galaktoboureko"],
    
    "South Korea": ["Kimchi", "Bibimbap", "Bulgogi", "Japchae", "Samgyeopsal",
                    "Tteokbokki", "Sundubu-jjigae", "Galbi", "Kimchi Jjigae", "Haemul Pajeon"],
    
    "France": ["Coq au Vin", "Bouillabaisse", "Ratatouille", "Quiche Lorraine", "Cassoulet",
               "Croissant", "Crème Brûlée", "Boeuf Bourguignon", "Escargots", "Tarte Tatin"],
    
    "Thailand": ["Pad Thai", "Tom Yum Goong", "Green Curry", "Massaman Curry", "Som Tam",
                 "Larb", "Khao Soi", "Panang Curry", "Pad Krapow", "Mango Sticky Rice"],
    
    "India": ["Butter Chicken", "Biryani", "Tandoori Chicken", "Palak Paneer", "Dal Makhani",
              "Samosas", "Chana Masala", "Rogan Josh", "Dosa", "Gulab Jamun"],
    
    "Spain": ["Paella", "Gazpacho", "Tortilla Española", "Jamón Ibérico", "Patatas Bravas",
              "Churros", "Croquetas", "Pulpo a la Gallega", "Albóndigas", "Crema Catalana"]
}

async def generate_all_recipes():
    """Generate 10 recipes per country (100 total)."""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    total_generated = 0
    total_rejected = 0
    
    try:
        for country_info in COUNTRIES:
            country = country_info["name"]
            region = country_info["region"]
            recipes = RECIPES_PER_COUNTRY.get(country, [])
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Generating recipes for {country} ({region})")
            logger.info(f"{'='*60}\n")
            
            for dish_name in recipes:
                try:
                    logger.info(f"Generating: {dish_name}...")
                    
                    # Generate recipe
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
                        total_rejected += 1
                        logger.warning(f"  ✗ REJECTED: {rejection_reason}")
                    else:
                        recipe_data['status'] = 'published'
                        await db.recipes.insert_one(recipe_data)
                        total_generated += 1
                        logger.info(f"  ✓ SUCCESS: {dish_name} ({recipe_data['slug']})")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"  ✗ ERROR generating {dish_name}: {str(e)}")
                    continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Generation Complete!")
        logger.info(f"Total Generated: {total_generated}")
        logger.info(f"Total Rejected: {total_rejected}")
        logger.info(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(generate_all_recipes())
