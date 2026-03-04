"""
AI Image Generation Service — Dish-Accurate Recipe Images (OpenAI Direct)

Uses OpenAI gpt-image-1 directly for realistic food photography.
Images generated lazily on first view, saved as WebP, served locally.
"""

import os
import base64
import logging
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

_gen_locks: Dict[str, float] = defaultdict(float)
_LOCK_TTL = 120

STATIC_DIR = Path(__file__).parent.parent / "static" / "recipe-images"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def _build_prompt(recipe: Dict[str, Any]) -> str:
    title = recipe.get("recipe_name") or recipe.get("title_original") or "dish"
    country = recipe.get("origin_country") or recipe.get("country") or ""
    region = recipe.get("origin_region") or recipe.get("region") or ""

    ingredients = recipe.get("ingredients", [])
    key_items = []
    for ing in ingredients[:6]:
        if isinstance(ing, dict):
            key_items.append(ing.get("item", ""))
        elif isinstance(ing, str):
            key_items.append(ing)
    ingredient_text = ", ".join(i for i in key_items if i)

    origin = f"{region}, {country}".strip(", ") if region else country

    prompt = f"Realistic food photography of {title}"
    if origin:
        prompt += f", traditional {origin} dish"
    if ingredient_text:
        prompt += f". Key ingredients: {ingredient_text}"
    prompt += (
        ". Authentic plating. Natural lighting. "
        "No text. No watermark. No logo. No people."
    )
    return prompt


def _build_alt(recipe: Dict[str, Any]) -> str:
    title = recipe.get("recipe_name") or recipe.get("title_original") or "Recipe"
    country = recipe.get("origin_country") or recipe.get("country")
    if country:
        return f"Traditional {title} from {country}"
    return f"Traditional {title}"


async def generate_recipe_image(recipe: Dict[str, Any]) -> Optional[Dict[str, str]]:
    slug = recipe.get("slug", "unknown")

    now = time.time()
    if now - _gen_locks.get(slug, 0) < _LOCK_TTL:
        logger.debug(f"Skipping AI gen for {slug} — lock active")
        return None
    _gen_locks[slug] = now

    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set")
            return None

        prompt = _build_prompt(recipe)
        logger.info(f"Generating AI image for {slug}")

        client = OpenAI(api_key=api_key)

        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
        )

        image_data = response.data[0]

        # gpt-image-1 returns b64_json by default
        if hasattr(image_data, "b64_json") and image_data.b64_json:
            image_bytes = base64.b64decode(image_data.b64_json)
        elif hasattr(image_data, "url") and image_data.url:
            import httpx
            r = httpx.get(image_data.url, timeout=30)
            r.raise_for_status()
            image_bytes = r.content
        else:
            logger.error(f"No image data returned for {slug}")
            return None

        # Save as WebP
        try:
            from PIL import Image
            img = Image.open(BytesIO(image_bytes))
            webp_path = STATIC_DIR / f"{slug}.webp"
            img.save(str(webp_path), "WEBP", quality=82)
            ext = ".webp"
        except ImportError:
            webp_path = STATIC_DIR / f"{slug}.png"
            with open(webp_path, "wb") as f:
                f.write(image_bytes)
            ext = ".png"

        logger.info(f"Saved image ({webp_path.stat().st_size // 1024}KB): {webp_path}")

        return {
            "url": f"/api/recipe-images/{slug}{ext}",
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
        _gen_locks.pop(slug, None)


async def auto_assign_ai_image(db, recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Assign an AI image if recipe has none. Never crashes."""
    if recipe.get("image_url"):
        return recipe

    slug = recipe.get("slug", "unknown")

    # Check disk first (race-condition guard)
    for ext in (".webp", ".png"):
        disk_path = STATIC_DIR / f"{slug}{ext}"
        if disk_path.exists():
            update = {
                "image_url": f"/api/recipe-images/{slug}{ext}",
                "image_alt": _build_alt(recipe),
                "image_source": "ai",
            }
            try:
                await db.recipes.update_one({"slug": slug}, {"$set": update})
                recipe.update(update)
            except Exception as e:
                logger.error(f"DB update failed for existing image {slug}: {e}")
            return recipe

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
