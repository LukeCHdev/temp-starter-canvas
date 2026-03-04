"""
AI Image Generation Service — Dish-Accurate Recipe Images

Generates realistic food photography using GPT Image 1 via Emergent integrations.
Images are generated lazily on first recipe view and stored permanently on disk.

Flow:
  1. Recipe requested → check DB for existing image_url
  2. If missing → generate via AI → save WebP to /static/recipe-images/{slug}.webp
  3. Update DB with image_url, image_alt, image_source='ai'
  4. Return updated recipe

Features:
  - Concurrency lock (prevents duplicate generation for same recipe)
  - Graceful failure (page loads even if generation fails)
  - Structured prompts using recipe data for dish accuracy
  - Cost-controlled: generate once, never again
"""

import os
import asyncio
import logging
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# Concurrency lock: slug -> timestamp
_gen_locks: Dict[str, float] = defaultdict(float)
_LOCK_TTL = 120  # 2 min — generation can take up to 60s

STATIC_DIR = Path(__file__).parent.parent / "static" / "recipe-images"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def _build_prompt(recipe: Dict[str, Any]) -> str:
    """Build a structured prompt that guarantees dish accuracy."""
    title = recipe.get("recipe_name") or recipe.get("title_original") or "dish"
    country = recipe.get("origin_country") or recipe.get("country") or ""
    region = recipe.get("origin_region") or recipe.get("region") or ""

    # Extract key ingredients for prompt specificity
    ingredients = recipe.get("ingredients", [])
    key_items = []
    for ing in ingredients[:6]:
        if isinstance(ing, dict):
            key_items.append(ing.get("item", ""))
        elif isinstance(ing, str):
            key_items.append(ing)
    ingredient_text = ", ".join(i for i in key_items if i)

    # Build location context
    origin = f"{region}, {country}".strip(", ") if region else country

    prompt = (
        f"Realistic food photography of {title}"
    )
    if origin:
        prompt += f", traditional {origin} dish"
    if ingredient_text:
        prompt += f". Key ingredients: {ingredient_text}"
    prompt += (
        ". Served on a plate or bowl appropriate for the dish. "
        "Natural light, high detail, overhead or 45-degree angle, "
        "no text, no watermark, no logo, no people, no utensils blocking the food. "
        "Authentic presentation, professional food styling."
    )
    return prompt


def _build_alt(recipe: Dict[str, Any]) -> str:
    title = recipe.get("recipe_name") or recipe.get("title_original") or "Recipe"
    country = recipe.get("origin_country") or recipe.get("country")
    if country:
        return f"AI-generated image of {title} from {country}"
    return f"AI-generated image of {title}"


async def generate_recipe_image(recipe: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Generate an AI image for a recipe and save it to disk.

    Returns dict with url/alt/source keys on success, None on failure.
    Never raises — all errors are caught and logged.
    """
    slug = recipe.get("slug", "unknown")

    # --- concurrency guard ---
    now = time.time()
    if now - _gen_locks.get(slug, 0) < _LOCK_TTL:
        logger.debug(f"Skipping AI gen for {slug} — lock active")
        return None
    _gen_locks[slug] = now

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            logger.warning("EMERGENT_LLM_KEY not set — cannot generate image")
            return None

        prompt = _build_prompt(recipe)
        logger.info(f"Generating AI image for {slug} — prompt: {prompt[:120]}…")

        gen = OpenAIImageGeneration(api_key=api_key)
        images = await gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
        )

        if not images or len(images) == 0:
            logger.warning(f"No image returned for {slug}")
            return None

        image_bytes = images[0]

        # Convert to WebP for smaller size
        try:
            from PIL import Image
            img = Image.open(BytesIO(image_bytes))
            webp_path = STATIC_DIR / f"{slug}.webp"
            img.save(str(webp_path), "WEBP", quality=82)
            logger.info(f"Saved WebP image ({webp_path.stat().st_size // 1024}KB): {webp_path}")
        except ImportError:
            # Pillow not available — save raw PNG
            webp_path = STATIC_DIR / f"{slug}.png"
            with open(webp_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Saved PNG image (Pillow unavailable): {webp_path}")

        # Build the URL path (served by FastAPI static mount)
        ext = webp_path.suffix  # .webp or .png
        image_url = f"/api/recipe-images/{slug}{ext}"

        return {
            "url": image_url,
            "alt": _build_alt(recipe),
            "source": "ai",
            "metadata": {
                "model": "gpt-image-1",
                "prompt_used": prompt,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"AI image generation failed for {slug}: {e}")
        return None
    finally:
        # Release lock after completion (not after TTL)
        _gen_locks.pop(slug, None)


async def auto_assign_ai_image(db, recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assign an AI-generated image to a recipe if it doesn't have one.

    This replaces the old Unsplash-based auto_assign_image.
    Never blocks or crashes — returns recipe as-is on any failure.
    """
    # Already has an image → skip
    if recipe.get("image_url"):
        return recipe

    # Check if file already exists on disk (race-condition guard)
    slug = recipe.get("slug", "unknown")
    for ext in (".webp", ".png"):
        disk_path = STATIC_DIR / f"{slug}{ext}"
        if disk_path.exists():
            image_url = f"/api/recipe-images/{slug}{ext}"
            update = {
                "image_url": image_url,
                "image_alt": _build_alt(recipe),
                "image_source": "ai",
            }
            try:
                await db.recipes.update_one({"slug": slug}, {"$set": update})
                recipe.update(update)
            except Exception as e:
                logger.error(f"DB update failed for existing image {slug}: {e}")
            return recipe

    # Generate new image
    result = await generate_recipe_image(recipe)

    if result:
        update = {
            "image_url": result["url"],
            "image_alt": result["alt"],
            "image_source": result["source"],
            "image_metadata": result["metadata"],
        }
        try:
            await db.recipes.update_one({"slug": slug}, {"$set": update})
            recipe.update(update)
            logger.info(f"AI image assigned to {slug}")
        except Exception as e:
            logger.error(f"DB update failed for {slug}: {e}")

    return recipe
