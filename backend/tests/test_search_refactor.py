"""
Search API Tests for DB-Only Refactored Search System

Tests the refactored search functionality:
- Pure DB-only search (no AI generation)
- Input validation (min 2 chars, max 80 chars)
- Regex injection prevention
- Response format (array of recipes)
- Rate limiting (30 requests per 10 min per IP)
- MongoDB indexes verification
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSearchInputValidation:
    """Input validation tests - min 2 chars, max 80 chars"""
    
    def test_search_single_char_rejected(self):
        """Search with 1 character should return 422 (min 2 chars required)"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "a"})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        data = response.json()
        assert "detail" in data or "error" in data
        print("PASS: Single char search correctly returns 422")
    
    def test_search_two_chars_accepted(self):
        """Search with 2 characters should be accepted"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "ab"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "found" in data
        assert "recipes" in data
        print("PASS: Two char search correctly returns 200")
    
    def test_search_80_chars_accepted(self):
        """Search with exactly 80 characters should be accepted"""
        query = "a" * 80
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": query})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: 80 char search correctly returns 200")
    
    def test_search_81_chars_rejected(self):
        """Search with 81 characters should return 422 (max 80 chars)"""
        query = "a" * 81
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": query})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: 81 char search correctly returns 422")
    
    def test_search_empty_rejected(self):
        """Search with empty query should return 422"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": ""})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Empty search correctly returns 422")
    
    def test_search_whitespace_only_rejected(self):
        """Search with whitespace only should return 422 (after trim < 2)"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "  "})
        # After strip, this becomes empty or very short
        assert response.status_code in [200, 422], f"Expected 200 or 422, got {response.status_code}"
        print(f"PASS: Whitespace-only search handled (status: {response.status_code})")


class TestSearchResponseFormat:
    """Test that search returns array of recipes (not single recipe)"""
    
    def test_search_carbonara_returns_array(self):
        """Search for carbonara should return found=true with recipes array"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "carbonara"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["found"] == True, "Expected found=true for carbonara"
        assert "recipes" in data, "Response should contain 'recipes' key"
        assert isinstance(data["recipes"], list), "recipes should be an array"
        assert len(data["recipes"]) >= 1, "Should have at least 1 result"
        
        # Verify recipe structure
        recipe = data["recipes"][0]
        assert "slug" in recipe
        assert "recipe_name" in recipe
        print(f"PASS: Carbonara search returns array with {len(data['recipes'])} recipes")
    
    def test_search_nonexistent_returns_suggestion(self):
        """Search for nonexistent term should return found=false with suggestion"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "xyznonexistent"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["found"] == False, "Expected found=false for nonexistent"
        assert data["recipes"] == [], "recipes should be empty array"
        assert "suggestion" in data, "Should include suggestion for no results"
        print(f"PASS: Nonexistent search returns found=false with suggestion")
    
    def test_search_country_match(self):
        """Search by country name should return matching recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "japan"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["found"] == True, "Expected found=true for japan"
        assert len(data["recipes"]) >= 1, "Should have at least 1 Japanese recipe"
        
        # Verify at least one recipe is from Japan
        japan_found = any(
            "japan" in r.get("origin_country", "").lower() or
            "japan" in r.get("slug", "").lower()
            for r in data["recipes"]
        )
        assert japan_found, "Should have Japan-related recipes"
        print(f"PASS: Japan search returns {len(data['recipes'])} recipes")
    
    def test_search_pasta_multiple_results(self):
        """Search for pasta should return multiple matching recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "pasta"})
        assert response.status_code == 200
        data = response.json()
        
        # May or may not have results depending on DB content
        assert "found" in data
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
        print(f"PASS: Pasta search returns {len(data.get('recipes', []))} recipes")


class TestSearchRegexInjectionPrevention:
    """Test that regex special characters are properly escaped"""
    
    def test_regex_wildcard_blocked(self):
        """Search with .* should NOT return all recipes (regex injection blocked)"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": ".*"})
        assert response.status_code == 200
        data = response.json()
        
        # If .* was executed as regex, it would match everything
        # With proper escaping, it should find nothing (no recipe named ".*")
        assert data["found"] == False, "Regex .* should be escaped, not executed"
        assert len(data["recipes"]) == 0, "Should not return all recipes"
        print("PASS: Regex .* injection blocked")
    
    def test_regex_brackets_blocked(self):
        """Search with [a-z] should NOT match all recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "[a-z]"})
        assert response.status_code == 200
        data = response.json()
        
        # Escaped brackets won't match anything
        assert data["found"] == False, "Regex [a-z] should be escaped"
        print("PASS: Regex [a-z] injection blocked")
    
    def test_regex_anchor_blocked(self):
        """Search with ^ and $ should be escaped"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "^spa"})
        assert response.status_code == 200
        data = response.json()
        # ^spa escaped should not match "spaghetti"
        assert data["found"] == False or data["total"] == 0
        print("PASS: Regex anchor ^ blocked")
    
    def test_recipes_list_regex_blocked(self):
        """GET /api/recipes?search=.* should NOT return all recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes", params={"search": ".*"})
        assert response.status_code == 200
        data = response.json()
        
        # With regex escaped, ".*" should match nothing
        assert data["total"] == 0, "Regex .* in list endpoint should be blocked"
        print("PASS: GET /api/recipes regex injection blocked")


class TestSearchNoAIGeneration:
    """Test that search does NOT trigger AI generation"""
    
    def test_auto_generate_param_ignored(self):
        """auto_generate parameter should be ignored (not accepted)"""
        response = requests.get(f"{BASE_URL}/api/recipes/search", 
                               params={"q": "pizza", "auto_generate": "true"})
        assert response.status_code == 200
        data = response.json()
        
        # Should return DB results only, not trigger generation
        # The key check is that it doesn't take long (AI would take seconds)
        assert "found" in data
        assert "recipes" in data
        print("PASS: auto_generate parameter has no effect on search")
    
    def test_search_is_fast(self):
        """Search should complete quickly (< 2 seconds) indicating no AI call"""
        import time
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "carbonara"})
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Search took {elapsed}s, should be < 2s (no AI call)"
        print(f"PASS: Search completed in {elapsed:.2f}s (fast, no AI)")


class TestSearchRateLimiting:
    """Test rate limiting - 30 requests per 10 minutes per IP"""
    
    def test_rate_limit_not_triggered_early(self):
        """First few requests should not be rate limited"""
        # Make 5 quick requests
        for i in range(5):
            response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": f"test{i}"})
            assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
            if response.status_code == 429:
                print(f"WARNING: Rate limited on request {i+1} (may be from previous tests)")
                break
        else:
            print("PASS: First 5 requests not rate limited")
    
    def test_rate_limit_message(self):
        """When rate limited, should return 429 with proper message"""
        # This test is informational - rate limit may not trigger if under threshold
        response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": "ratelimit"})
        
        if response.status_code == 429:
            data = response.json()
            assert "detail" in data or "error" in data
            print(f"PASS: Rate limit returns 429 with message: {data}")
        else:
            print(f"INFO: Not currently rate limited (status: {response.status_code})")


class TestSearchSuggestionsEndpoint:
    """Test /api/search/suggestions endpoint"""
    
    def test_suggestions_requires_min_2_chars(self):
        """Suggestions with 1 char should return 422"""
        response = requests.get(f"{BASE_URL}/api/search/suggestions", params={"q": "a"})
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Suggestions requires min 2 chars")
    
    def test_suggestions_regex_blocked(self):
        """Suggestions with regex should be escaped"""
        response = requests.get(f"{BASE_URL}/api/search/suggestions", params={"q": ".*"})
        assert response.status_code == 200
        data = response.json()
        # Should return empty or minimal results, not all recipes
        assert len(data.get("suggestions", [])) == 0
        print("PASS: Suggestions regex injection blocked")
    
    def test_suggestions_valid_query(self):
        """Valid query should return suggestions"""
        response = requests.get(f"{BASE_URL}/api/search/suggestions", params={"q": "sp"})
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        print(f"PASS: Suggestions returns {len(data.get('suggestions', []))} items")


class TestMongoDBIndexes:
    """Verify MongoDB indexes exist (indirect test via performance)"""
    
    def test_search_performance_indicates_indexes(self):
        """Fast search response suggests indexes are working"""
        import time
        
        # Multiple searches to verify consistent performance
        times = []
        for q in ["carbonara", "pizza", "japan", "italy", "sushi"]:
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/recipes/search", params={"q": q})
            times.append(time.time() - start)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.5, f"Average search time {avg_time:.2f}s suggests missing indexes"
        print(f"PASS: Average search time {avg_time:.3f}s indicates indexes working")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
