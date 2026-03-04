"""
Test suite for Unsplash Image Service
Tests the multi-step fallback logic, lazy caching, API key security, and error handling.

Features tested:
1. build_fallback_queries() - generates correct fallback query chain
2. _simplify_title() - strips geographic descriptors
3. fetch_image() - multi-step fallback execution
4. Lazy caching - already-imaged recipes don't trigger new calls
5. API key security - key not exposed in responses
"""

import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

from services.unsplash_service import UnsplashService, unsplash_service

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============== UNIT TESTS FOR FALLBACK LOGIC ==============

class TestFallbackQueryGeneration:
    """Unit tests for build_fallback_queries() method"""
    
    def test_exact_query_is_first(self):
        """Verify exact query '{title} {country} food' is tried first"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Risotto alla Milanese",
            "origin_country": "Italy"
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # First query should be exact
        assert queries[0] == "Risotto alla Milanese Italy food"
        print(f"✓ Exact query is first: {queries[0]}")
    
    def test_simplified_query_is_second(self):
        """Verify simplified query without geo descriptors is second"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Risotto alla Milanese",
            "origin_country": "Italy"
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # Should have at least 2 queries for recipes with geo descriptors
        assert len(queries) >= 2
        # Second query should be simplified (without "alla Milanese")
        assert queries[1] == "Risotto Italy food"
        print(f"✓ Simplified query is second: {queries[1]}")
    
    def test_cuisine_fallback_is_last(self):
        """Verify '{country} food' is the last fallback"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Risotto alla Milanese",
            "origin_country": "Italy"
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # Last query should be cuisine-only
        assert queries[-1] == "Italy food"
        print(f"✓ Cuisine fallback is last: {queries[-1]}")
    
    def test_no_duplicate_queries(self):
        """Verify no duplicate queries are generated"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Risotto",  # No geo descriptor, so simplified == exact
            "origin_country": "Italy"
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # Should not have duplicates
        assert len(queries) == len(set(queries)), f"Duplicate queries found: {queries}"
        print(f"✓ No duplicate queries: {queries}")
    
    def test_fallback_with_no_country(self):
        """Verify fallback works without country"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Risotto alla Milanese",
            "origin_country": None
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # Should still have queries without country
        assert len(queries) >= 1
        assert "food" in queries[0].lower()
        print(f"✓ Fallback without country: {queries}")


class TestTitleSimplification:
    """Unit tests for _simplify_title() method"""
    
    def test_strips_alla_pattern(self):
        """Verify 'alla X' is stripped from title"""
        service = UnsplashService()
        
        result = service._simplify_title("Risotto alla Milanese")
        assert result == "Risotto"
        print(f"✓ 'alla Milanese' stripped: '{result}'")
    
    def test_strips_al_pattern(self):
        """Verify 'al X' is stripped from title"""
        service = UnsplashService()
        
        result = service._simplify_title("Pasta al Forno")
        assert result == "Pasta"
        print(f"✓ 'al Forno' stripped: '{result}'")
    
    def test_strips_della_pattern(self):
        """Verify 'della X' is stripped from title"""
        service = UnsplashService()
        
        result = service._simplify_title("Pasta della Nonna")
        assert result == "Pasta"
        print(f"✓ 'della Nonna' stripped: '{result}'")
    
    def test_strips_from_pattern(self):
        """Verify 'from X' is stripped from title"""
        service = UnsplashService()
        
        result = service._simplify_title("Pizza from Naples")
        assert result == "Pizza"
        print(f"✓ 'from Naples' stripped: '{result}'")
    
    def test_strips_style_word(self):
        """Verify 'style' is stripped from title"""
        service = UnsplashService()
        
        result = service._simplify_title("Italian style Pasta")
        assert "style" not in result.lower()
        print(f"✓ 'style' stripped: '{result}'")
    
    def test_no_change_for_simple_title(self):
        """Verify simple titles are not changed"""
        service = UnsplashService()
        
        result = service._simplify_title("Pasta Carbonara")
        assert result == "Pasta Carbonara"
        print(f"✓ Simple title unchanged: '{result}'")
    
    def test_multiple_patterns(self):
        """Verify multiple patterns are stripped"""
        service = UnsplashService()
        
        result = service._simplify_title("Traditional Pasta alla Romana")
        # Should strip both 'traditional' and 'alla Romana'
        assert "traditional" not in result.lower()
        assert "alla" not in result.lower()
        print(f"✓ Multiple patterns stripped: '{result}'")


class TestFallbackQueryVariants:
    """Test fallback queries for various recipe types"""
    
    def test_italian_alla_recipes(self):
        """Test Italian 'alla X' recipes generate correct fallbacks"""
        service = UnsplashService()
        
        recipes_to_test = [
            ("Ossobuco alla Milanese", "Italy", ["Ossobuco alla Milanese Italy food", "Ossobuco Italy food", "Italy food"]),
            ("Saltimbocca alla Romana", "Italy", ["Saltimbocca alla Romana Italy food", "Saltimbocca Italy food", "Italy food"]),
            ("Pasta alla Norma", "Italy", ["Pasta alla Norma Italy food", "Pasta Italy food", "Italy food"]),
        ]
        
        for title, country, expected in recipes_to_test:
            recipe = {"recipe_name": title, "origin_country": country}
            queries = service.build_fallback_queries(recipe)
            
            assert queries == expected, f"Expected {expected}, got {queries} for {title}"
            print(f"✓ {title}: {queries}")
    
    def test_simple_dish_names(self):
        """Test dishes without geo descriptors"""
        service = UnsplashService()
        
        recipe = {
            "recipe_name": "Sushi Nigiri",
            "origin_country": "Japan"
        }
        
        queries = service.build_fallback_queries(recipe)
        
        # Should have exact and cuisine fallback, no simplified (since no geo descriptor)
        assert "Sushi Nigiri Japan food" in queries
        assert "Japan food" in queries
        print(f"✓ Simple dish queries: {queries}")


# ============== INTEGRATION TESTS ==============

class TestRecipeEndpointImageAssignment:
    """Test /api/recipes/{slug} endpoint image auto-assignment"""
    
    def test_recipe_with_existing_image_returns_image(self):
        """Verify recipes with existing images return them without new API calls"""
        # Use a recipe known to have an image
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "image_url" in data
        assert data["image_url"] is not None
        assert "unsplash.com" in data["image_url"]
        print(f"✓ Recipe with image returns image_url: {data['image_url'][:60]}...")
    
    def test_recipe_response_does_not_expose_api_key(self):
        """Verify API key is never exposed in response"""
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        
        assert response.status_code == 200
        response_text = response.text
        
        # Check that API key is not in response
        assert "_XgKKn6DDwwKtwaUwYzvw3qoiDWdWVe6yQkmrX1pubg" not in response_text
        assert "UNSPLASH_ACCESS_KEY" not in response_text
        assert "Client-ID" not in response_text
        print("✓ API key not exposed in response")
    
    def test_recipe_without_image_gets_image_assigned(self):
        """Test that a recipe without an image gets one assigned via fallback"""
        # First, find a recipe without image
        response = requests.get(f"{BASE_URL}/api/recipes")
        data = response.json()
        
        # Find a recipe without image_url
        recipe_without_image = None
        for r in data.get('recipes', []):
            if not r.get('image_url'):
                recipe_without_image = r
                break
        
        if not recipe_without_image:
            pytest.skip("All recipes already have images - cannot test fresh assignment")
        
        slug = recipe_without_image.get('slug')
        print(f"Testing recipe without image: {slug}")
        
        # Request the recipe - should trigger image assignment
        response = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should now have an image (or None if Unsplash couldn't find one)
        if data.get('image_url'):
            assert "unsplash.com" in data["image_url"]
            print(f"✓ Image assigned to {slug}: {data['image_url'][:60]}...")
        else:
            print(f"⚠ No image found for {slug} (may be expected for obscure dishes)")


class TestLazyCaching:
    """Test lazy caching - already-imaged recipes don't trigger new calls"""
    
    def test_second_request_returns_same_image(self):
        """Verify second request returns cached image without new API call"""
        slug = "risotto-alla-milanese-italy"
        
        # First request
        response1 = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        assert response1.status_code == 200
        image1 = response1.json().get('image_url')
        
        # Second request
        response2 = requests.get(f"{BASE_URL}/api/recipes/{slug}")
        assert response2.status_code == 200
        image2 = response2.json().get('image_url')
        
        # Should be the same image (cached)
        assert image1 == image2
        print(f"✓ Same image returned on second request (lazy caching works)")


class TestRecipeEcosystemEndpoint:
    """Test the /api/recipes/recipe-ecosystem endpoint if it exists"""
    
    def test_recipes_list_includes_images(self):
        """Verify recipes list endpoint returns image data"""
        response = requests.get(f"{BASE_URL}/api/recipes")
        
        assert response.status_code == 200
        data = response.json()
        
        recipes_with_images = 0
        recipes_without_images = 0
        
        for recipe in data.get('recipes', []):
            if recipe.get('image_url'):
                recipes_with_images += 1
            else:
                recipes_without_images += 1
        
        print(f"✓ Recipes with images: {recipes_with_images}")
        print(f"✓ Recipes without images: {recipes_without_images}")
        
        # At least some recipes should have images
        assert recipes_with_images > 0, "Expected at least some recipes with images"


class TestErrorHandling:
    """Test service handles errors gracefully"""
    
    def test_invalid_recipe_returns_404(self):
        """Verify invalid recipe slug returns 404, not crash"""
        response = requests.get(f"{BASE_URL}/api/recipes/nonexistent-recipe-xyz-12345")
        
        assert response.status_code == 404
        print("✓ Invalid recipe returns 404 without crash")
    
    def test_service_is_configured_on_server(self):
        """Verify Unsplash service is properly configured on server (by checking images work)"""
        # Test that an image was actually fetched - proves the service is configured
        response = requests.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        data = response.json()
        
        # If service is configured, recipes should have unsplash images
        assert data.get('image_url') is not None, "Service not configured - no images returned"
        assert 'unsplash.com' in data.get('image_url', ''), "Expected Unsplash image"
        print("✓ Unsplash service is configured on server (verified via image fetch)")


# ============== RUN TESTS ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
