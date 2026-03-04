"""
Clear all Unsplash-sourced images from recipes.

This resets image_url, image_alt, image_source, image_metadata
for every recipe where image_source='unsplash', so they can be
regenerated with AI on next view.

Usage: python scripts/clear_unsplash_images.py
"""

import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


async def main():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    result = await db.recipes.update_many(
        {"image_source": "unsplash"},
        {"$unset": {
            "image_url": "",
            "image_alt": "",
            "image_source": "",
            "image_metadata": "",
        }}
    )
    print(f"Cleared Unsplash images from {result.modified_count} recipes.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
