"""
Script to assign Unsplash images to all recipes without images.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import the auto_assign_image function
from services.unsplash_service import auto_assign_image, unsplash_service

async def assign_images_to_all_recipes():
    """Assign images to all recipes that don't have one."""
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Check if Unsplash is configured
    if not unsplash_service.is_configured:
        print("❌ UNSPLASH_ACCESS_KEY not configured!")
        return
    
    print("🖼️  Starting image assignment for recipes...")
    
    # Get all recipes without images
    recipes = await db.recipes.find(
        {
            "status": "published",
            "$or": [
                {"image_url": {"$exists": False}},
                {"image_url": None},
                {"image_url": ""}
            ]
        },
        {"_id": 0}
    ).to_list(500)
    
    print(f"📋 Found {len(recipes)} recipes without images")
    
    success_count = 0
    fail_count = 0
    
    for recipe in recipes:
        slug = recipe.get('slug', 'unknown')
        name = recipe.get('recipe_name', slug)
        
        print(f"  Processing: {name}...", end=" ")
        
        updated_recipe = await auto_assign_image(db, recipe)
        
        if updated_recipe.get('image_url'):
            print("✅")
            success_count += 1
        else:
            print("❌ (no image found)")
            fail_count += 1
        
        # Rate limit - wait 1 second between requests
        await asyncio.sleep(1)
    
    print(f"\n✨ Image assignment complete!")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    
    # Close connections
    await unsplash_service.close()
    client.close()

if __name__ == "__main__":
    asyncio.run(assign_images_to_all_recipes())
