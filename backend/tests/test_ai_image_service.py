"""
AI Image Service Tests - Verify AI-generated recipe images functionality

Tests cover:
- Recipe API returns image_url, image_alt, image_source='ai'
- image_url is relative path like /api/recipe-images/{slug}.webp
- Static file serving returns 200 with content-type image/webp
- Recipes without images load correctly (graceful handling)
- Second request returns same cached image (no duplicate generation)
- Translation API includes image_url in metadata
- No API keys exposed in responses
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Known recipes WITH AI images (pre-generated)
RECIPES_WITH_IMAGES = [
    "pizza-margherita-italy",
    "risotto-alla-milanese-italy",
    "coq-au-vin-france",
]

# Known recipes that may not have images yet
RECIPES_POSSIBLY_WITHOUT_IMAGES = [
    "tonkotsu-ramen-japan",
    "tacos-al-pastor-mexico",
]


class TestAIImageRecipeAPI:
    """Test that recipe API returns correct AI image data"""

    def test_recipe_with_ai_image_returns_image_url(self):
        """Verify recipes with AI images return correct image_url"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200, f"Recipe API failed: {response.text}"
        data = response.json()
        
        # Verify image_url is present and correct format
        assert "image_url" in data, "image_url field missing"
        assert data["image_url"] is not None, "image_url should not be null"
        assert data["image_url"].startswith("/api/recipe-images/"), f"image_url should be relative path, got: {data['image_url']}"
        assert data["image_url"].endswith(".webp"), f"image_url should end with .webp, got: {data['image_url']}"
        
        print(f"PASS: Recipe {slug} has image_url: {data['image_url']}")

    def test_recipe_returns_image_alt(self):
        """Verify recipe API returns image_alt text"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "image_alt" in data, "image_alt field missing"
        assert data["image_alt"] is not None, "image_alt should not be null"
        assert len(data["image_alt"]) > 5, f"image_alt too short: {data['image_alt']}"
        
        print(f"PASS: image_alt = '{data['image_alt']}'")

    def test_recipe_returns_image_source_ai(self):
        """Verify image_source is 'ai' for AI-generated images"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "image_source" in data, "image_source field missing"
        assert data["image_source"] == "ai", f"Expected image_source='ai', got: {data['image_source']}"
        
        print(f"PASS: image_source = '{data['image_source']}'")

    @pytest.mark.parametrize("slug", RECIPES_WITH_IMAGES)
    def test_all_known_ai_images(self, slug):
        """Verify all known AI-generated recipes have correct image data"""
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("image_url"), f"Recipe {slug} missing image_url"
        assert data.get("image_source") == "ai", f"Recipe {slug} image_source != 'ai'"
        assert data.get("image_alt"), f"Recipe {slug} missing image_alt"
        
        print(f"PASS: {slug} - image_url={data['image_url']}, image_source={data['image_source']}")


class TestStaticImageServing:
    """Test that static image files are served correctly"""

    def test_static_image_returns_200(self):
        """Verify static image endpoint returns 200"""
        url = f"{BASE_URL}/api/recipe-images/pizza-margherita-italy.webp"
        response = requests.head(url)
        
        assert response.status_code == 200, f"Static image not found: {response.status_code}"
        print(f"PASS: Static image returns 200")

    def test_static_image_content_type_webp(self):
        """Verify static image has correct content-type"""
        url = f"{BASE_URL}/api/recipe-images/pizza-margherita-italy.webp"
        response = requests.head(url)
        
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "image/webp" in content_type, f"Expected image/webp, got: {content_type}"
        
        print(f"PASS: content-type = {content_type}")

    def test_static_image_has_content_length(self):
        """Verify static image has reasonable size"""
        url = f"{BASE_URL}/api/recipe-images/pizza-margherita-italy.webp"
        response = requests.head(url)
        
        assert response.status_code == 200
        content_length = int(response.headers.get("content-length", 0))
        assert content_length > 10000, f"Image too small: {content_length} bytes"
        
        print(f"PASS: content-length = {content_length} bytes")

    @pytest.mark.parametrize("slug", RECIPES_WITH_IMAGES)
    def test_all_static_images_accessible(self, slug):
        """Verify all known AI images are accessible via static route"""
        url = f"{BASE_URL}/api/recipe-images/{slug}.webp"
        response = requests.head(url)
        
        assert response.status_code == 200, f"Image not accessible: {slug}"
        print(f"PASS: {slug}.webp is accessible")


class TestGracefulFallback:
    """Test recipes without images load correctly"""

    def test_recipes_list_handles_missing_images(self):
        """Verify recipes list returns even for recipes without images"""
        response = requests.get(f"{BASE_URL}/api/recipes/top-worldwide?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recipes" in data
        assert len(data["recipes"]) > 0
        
        # Count recipes with and without images
        with_images = sum(1 for r in data["recipes"] if r.get("image_url"))
        without_images = sum(1 for r in data["recipes"] if not r.get("image_url"))
        
        print(f"PASS: Recipes list returned - {with_images} with images, {without_images} without")

    def test_recipe_without_image_still_loads(self):
        """Verify recipe without image returns 200 (graceful handling)"""
        # Find a recipe without an image from the list
        response = requests.get(f"{BASE_URL}/api/recipes/top-worldwide?limit=10")
        data = response.json()
        
        # Find recipe without image
        recipe_without_image = None
        for r in data.get("recipes", []):
            if not r.get("image_url"):
                recipe_without_image = r.get("slug")
                break
        
        if recipe_without_image:
            # Fetch the recipe directly
            recipe_response = requests.get(f"{BASE_URL}/api/recipes/{recipe_without_image}")
            assert recipe_response.status_code == 200, f"Recipe without image failed to load"
            recipe_data = recipe_response.json()
            
            # Should have slug and recipe_name even without image
            assert recipe_data.get("slug") == recipe_without_image
            assert recipe_data.get("recipe_name")
            
            print(f"PASS: Recipe {recipe_without_image} loads correctly without image")
        else:
            print("SKIP: All recipes have images - no recipe without image to test")


class TestImageCaching:
    """Test that second request returns same cached image"""

    def test_second_request_returns_same_image(self):
        """Verify requesting same recipe twice returns identical image_url"""
        slug = "pizza-margherita-italy"
        
        # First request
        response1 = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        assert response1.status_code == 200
        image_url_1 = response1.json().get("image_url")
        
        # Small delay
        time.sleep(0.5)
        
        # Second request
        response2 = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        assert response2.status_code == 200
        image_url_2 = response2.json().get("image_url")
        
        # Should be identical
        assert image_url_1 == image_url_2, f"Image URLs differ: {image_url_1} vs {image_url_2}"
        
        print(f"PASS: Image URL persists across requests: {image_url_1}")


class TestTranslationAPIIncludesImage:
    """Test that translation API includes image data in metadata"""

    def test_translation_api_includes_image_url(self):
        """Verify translation API returns image_url in metadata"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/translations/recipe/{slug}?lang=en")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metadata" in data, "metadata field missing"
        metadata = data["metadata"]
        
        assert metadata.get("image_url"), f"image_url missing in metadata: {metadata}"
        assert metadata.get("image_url").startswith("/api/recipe-images/")
        
        print(f"PASS: Translation API includes image_url: {metadata['image_url']}")

    def test_translation_api_includes_image_source(self):
        """Verify translation API returns image_source in metadata"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/translations/recipe/{slug}?lang=en")
        
        assert response.status_code == 200
        data = response.json()
        
        metadata = data.get("metadata", {})
        assert metadata.get("image_source") == "ai", f"Expected image_source='ai', got: {metadata.get('image_source')}"
        
        print(f"PASS: Translation API includes image_source: {metadata['image_source']}")

    def test_translation_api_includes_image_alt(self):
        """Verify translation API returns image_alt in metadata"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/translations/recipe/{slug}?lang=en")
        
        assert response.status_code == 200
        data = response.json()
        
        metadata = data.get("metadata", {})
        assert metadata.get("image_alt"), f"image_alt missing in metadata"
        
        print(f"PASS: Translation API includes image_alt: {metadata['image_alt']}")


class TestAPIKeySecurity:
    """Test that no API keys are exposed in responses"""

    def test_no_api_key_in_recipe_response(self):
        """Verify OPENAI_API_KEY is not exposed in recipe response"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        response_text = response.text.lower()
        
        # Check for common API key patterns
        assert "sk-" not in response_text, "API key pattern 'sk-' found in response"
        assert "api_key" not in response_text, "'api_key' found in response"
        assert "openai_api" not in response_text, "'openai_api' found in response"
        
        print("PASS: No API keys exposed in recipe response")

    def test_no_api_key_in_translation_response(self):
        """Verify OPENAI_API_KEY is not exposed in translation response"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/translations/recipe/{slug}?lang=en")
        
        assert response.status_code == 200
        response_text = response.text.lower()
        
        assert "sk-" not in response_text, "API key pattern found in translation response"
        
        print("PASS: No API keys exposed in translation response")

    def test_image_metadata_does_not_expose_secrets(self):
        """Verify image_metadata doesn't contain sensitive data"""
        slug = "pizza-margherita-italy"
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        
        metadata = data.get("image_metadata", {})
        metadata_str = str(metadata).lower()
        
        # Should not contain sensitive info
        assert "sk-" not in metadata_str, "API key in image_metadata"
        assert "api_key" not in metadata_str, "api_key in image_metadata"
        
        # But should contain expected fields
        if metadata:
            assert "model" in metadata or "prompt_used" in metadata or "generated_at" in metadata
        
        print(f"PASS: image_metadata is safe: {list(metadata.keys()) if metadata else 'empty'}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
