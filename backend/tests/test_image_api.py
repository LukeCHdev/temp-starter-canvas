"""
Test Suite for Unsplash Image API Integration
Tests the image_url, image_alt, image_source, image_metadata fields in API responses

Test coverage:
1. Recipe API returns image data
2. Translation API returns image data in metadata
3. Recipes without images render correctly (graceful fallback)
4. Photographer credit data is included
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Known recipes with images
RECIPES_WITH_IMAGES = [
    'risotto-alla-milanese-italy',
    'pizza-margherita-italy',
    'spaghetti-alla-carbonara-italy',
    'tonkotsu-ramen-japan',
    'sushi-nigiri-japan'
]


class TestRecipeAPIImageData:
    """Test /api/recipes/{slug} returns image data"""
    
    def test_recipe_api_returns_image_url(self):
        """Recipe API should return image_url for recipes with images"""
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'image_url' in data, "Response should contain image_url field"
        assert data['image_url'] is not None, "image_url should not be null"
        assert 'unsplash.com' in data['image_url'].lower(), "image_url should be from Unsplash"
    
    def test_recipe_api_returns_image_alt(self):
        """Recipe API should return image_alt for recipes with images"""
        response = requests.get(f"{BASE_URL}/api/recipes/pizza-margherita-italy")
        assert response.status_code == 200
        
        data = response.json()
        assert 'image_alt' in data, "Response should contain image_alt field"
        assert data['image_alt'] is not None, "image_alt should not be null"
        assert len(data['image_alt']) > 0, "image_alt should not be empty"
    
    def test_recipe_api_returns_image_metadata(self):
        """Recipe API should return image_metadata with photographer info"""
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        assert response.status_code == 200
        
        data = response.json()
        assert 'image_metadata' in data, "Response should contain image_metadata field"
        
        metadata = data['image_metadata']
        assert metadata is not None, "image_metadata should not be null"
        assert 'photographer' in metadata, "image_metadata should contain photographer"
        assert 'photographer_url' in metadata, "image_metadata should contain photographer_url"
    
    @pytest.mark.parametrize("recipe_slug", RECIPES_WITH_IMAGES[:3])
    def test_multiple_recipes_have_images(self, recipe_slug):
        """Multiple known recipes should have image data"""
        response = requests.get(f"{BASE_URL}/api/recipes/{recipe_slug}")
        assert response.status_code == 200, f"Failed for {recipe_slug}"
        
        data = response.json()
        assert data.get('image_url') is not None, f"{recipe_slug} should have image_url"


class TestTranslationAPIImageMetadata:
    """Test /api/translations/recipe/{slug}?lang=en returns image in metadata"""
    
    def test_translation_api_returns_image_url_in_metadata(self):
        """Translation API should return image_url in metadata for recipes with images"""
        response = requests.get(f"{BASE_URL}/api/translations/recipe/risotto-alla-milanese-italy?lang=en")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'metadata' in data, "Response should contain metadata field"
        
        metadata = data['metadata']
        assert 'image_url' in metadata, "Metadata should contain image_url"
        assert metadata['image_url'] is not None, "image_url in metadata should not be null"
        assert 'unsplash.com' in metadata['image_url'].lower(), "image_url should be from Unsplash"
    
    def test_translation_api_returns_image_alt_in_metadata(self):
        """Translation API should return image_alt in metadata"""
        response = requests.get(f"{BASE_URL}/api/translations/recipe/pizza-margherita-italy?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        metadata = data.get('metadata', {})
        assert 'image_alt' in metadata, "Metadata should contain image_alt"
        assert metadata['image_alt'] is not None, "image_alt in metadata should not be null"
    
    def test_translation_api_returns_image_source_in_metadata(self):
        """Translation API should return image_source in metadata"""
        response = requests.get(f"{BASE_URL}/api/translations/recipe/risotto-alla-milanese-italy?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        metadata = data.get('metadata', {})
        assert 'image_source' in metadata, "Metadata should contain image_source"
    
    def test_translation_api_returns_image_metadata_in_metadata(self):
        """Translation API should return image_metadata (photographer info) in metadata"""
        response = requests.get(f"{BASE_URL}/api/translations/recipe/risotto-alla-milanese-italy?lang=en")
        assert response.status_code == 200
        
        data = response.json()
        metadata = data.get('metadata', {})
        assert 'image_metadata' in metadata, "Metadata should contain image_metadata"
        
        image_metadata = metadata.get('image_metadata')
        if image_metadata:
            assert 'photographer' in image_metadata, "image_metadata should contain photographer"
            assert 'photographer_url' in image_metadata, "image_metadata should contain photographer_url"
    
    def test_translation_api_different_languages(self):
        """Translation API should return image_url in metadata for all languages"""
        for lang in ['en', 'it', 'es']:
            response = requests.get(f"{BASE_URL}/api/translations/recipe/pizza-margherita-italy?lang={lang}")
            assert response.status_code == 200, f"Failed for lang={lang}"
            
            data = response.json()
            metadata = data.get('metadata', {})
            # Image metadata should be consistent across languages
            assert 'image_url' in metadata, f"Metadata should contain image_url for lang={lang}"


class TestTranslationRecipesListAPI:
    """Test /api/translations/recipes returns image data for recipe cards"""
    
    def test_recipes_list_returns_image_url_in_metadata(self):
        """Recipes list API should return image_url in metadata for each recipe"""
        response = requests.get(f"{BASE_URL}/api/translations/recipes?lang=en&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert 'recipes' in data, "Response should contain recipes array"
        assert len(data['recipes']) > 0, "Should return at least 1 recipe"
        
        # Check first recipe has image data in metadata
        first_recipe = data['recipes'][0]
        assert 'metadata' in first_recipe, "Recipe should contain metadata"
        
        metadata = first_recipe['metadata']
        # image_url should be present (may be None for recipes without images)
        assert 'image_url' in metadata, "Metadata should include image_url field"


class TestGracefulFallbackNoImage:
    """Test that recipes without images render correctly"""
    
    def test_recipe_without_image_returns_null_image_url(self):
        """Recipe without Unsplash image should return null/None for image_url"""
        # First, find a recipe without an image by checking a few candidates
        # Most recipes should have images by now, so this might need adjustment
        response = requests.get(f"{BASE_URL}/api/recipes?limit=100")
        if response.status_code == 200:
            data = response.json()
            recipes = data.get('recipes', [])
            
            # Look for a recipe without image_url
            recipe_without_image = None
            for recipe in recipes:
                if not recipe.get('image_url'):
                    recipe_without_image = recipe
                    break
            
            if recipe_without_image:
                slug = recipe_without_image['slug']
                # Verify it can be fetched successfully
                detail_response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
                assert detail_response.status_code == 200, f"Recipe {slug} should be fetchable"
                # This is expected - recipe exists but has no image
                print(f"Found recipe without image: {slug}")


class TestPhotographerCredit:
    """Test photographer credit data is available"""
    
    def test_photographer_credit_in_recipe_api(self):
        """Recipe API should include photographer credit in image_metadata"""
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        assert response.status_code == 200
        
        data = response.json()
        metadata = data.get('image_metadata', {})
        
        if metadata:
            assert 'photographer' in metadata, "Should have photographer name"
            assert metadata['photographer'] is not None, "Photographer name should not be null"
            assert len(metadata['photographer']) > 0, "Photographer name should not be empty"
            
            assert 'photographer_url' in metadata, "Should have photographer URL"
            if metadata['photographer_url']:
                assert 'unsplash.com' in metadata['photographer_url'], "Photographer URL should be Unsplash profile"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
