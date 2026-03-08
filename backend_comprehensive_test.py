#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for Sous Chef Linguine Recipe App
Tests all major API endpoints as specified in the review request.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://mongo-link-verify.preview.emergentagent.com/api"

class SousChefBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Dict = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_health_check(self):
        """Test 1: Health Check - GET /api/"""
        print("\n=== Test 1: Health Check ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            
            if response.status_code != 200:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Health Check", False, "Invalid JSON response")
                return False
                
            # Check for expected fields in health check response
            if "message" not in data or "status" not in data:
                self.log_test("Health Check", False, f"Missing expected fields in response: {data}")
                return False
                
            self.log_test("Health Check", True, f"Status: {data.get('status')}, Message: {data.get('message')}")
            return True
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
            
    def test_top_worldwide_recipes(self):
        """Test 2: Top Worldwide Recipes - GET /api/recipes/top-worldwide?limit=5"""
        print("\n=== Test 2: Top Worldwide Recipes ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/top-worldwide?limit=5")
            
            if response.status_code != 200:
                self.log_test("Top Worldwide Recipes", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Top Worldwide Recipes", False, "Invalid JSON response")
                return False
                
            if "recipes" not in data:
                self.log_test("Top Worldwide Recipes", False, "Missing 'recipes' field in response")
                return False
                
            recipes = data["recipes"]
            
            if not isinstance(recipes, list):
                self.log_test("Top Worldwide Recipes", False, "'recipes' is not a list")
                return False
                
            if len(recipes) == 0:
                self.log_test("Top Worldwide Recipes", False, "No recipes returned")
                return False
                
            # Check first recipe structure
            first_recipe = recipes[0]
            required_fields = ["recipe_name", "slug", "origin_country"]
            missing_fields = [field for field in required_fields if field not in first_recipe]
            
            if missing_fields:
                self.log_test("Top Worldwide Recipes", False, f"Missing required fields: {missing_fields}")
                return False
                
            # Check for image_url field
            has_image_url = any(recipe.get("image_url") for recipe in recipes)
            image_status = "with image_url" if has_image_url else "missing image_url"
            
            self.log_test("Top Worldwide Recipes", True, 
                f"Returned {len(recipes)} recipes {image_status}")
            return True
            
        except Exception as e:
            self.log_test("Top Worldwide Recipes", False, f"Exception: {str(e)}")
            return False
            
    def test_featured_recipes(self):
        """Test 3: Featured Recipes - GET /api/recipes/featured?limit=4"""
        print("\n=== Test 3: Featured Recipes ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/featured?limit=4")
            
            if response.status_code != 200:
                self.log_test("Featured Recipes", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Featured Recipes", False, "Invalid JSON response")
                return False
                
            if "recipes" not in data:
                self.log_test("Featured Recipes", False, "Missing 'recipes' field in response")
                return False
                
            recipes = data["recipes"]
            
            if not isinstance(recipes, list):
                self.log_test("Featured Recipes", False, "'recipes' is not a list")
                return False
                
            # Check recipe structure and image_url
            has_image_url = False
            valid_structure = True
            
            for recipe in recipes:
                if not recipe.get("recipe_name") or not recipe.get("slug"):
                    valid_structure = False
                    break
                if recipe.get("image_url"):
                    has_image_url = True
                    
            if not valid_structure:
                self.log_test("Featured Recipes", False, "Invalid recipe structure")
                return False
                
            image_status = "with image_url" if has_image_url else "missing image_url"
            self.log_test("Featured Recipes", True, 
                f"Returned {len(recipes)} recipes {image_status}")
            return True
            
        except Exception as e:
            self.log_test("Featured Recipes", False, f"Exception: {str(e)}")
            return False
            
    def test_specific_recipe(self):
        """Test 4: Specific Recipe - GET /api/recipes/spaghetti-alla-carbonara-italy"""
        print("\n=== Test 4: Specific Recipe (Spaghetti Carbonara) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/spaghetti-alla-carbonara-italy")
            
            if response.status_code == 404:
                self.log_test("Specific Recipe", False, "Recipe not found (404) - may need to be seeded")
                return False
            elif response.status_code != 200:
                self.log_test("Specific Recipe", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Specific Recipe", False, "Invalid JSON response")
                return False
                
            # Check required fields for a recipe
            required_fields = ["recipe_name", "slug", "origin_country"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Specific Recipe", False, f"Missing required fields: {missing_fields}")
                return False
                
            # Check for image_url specifically
            has_image = "image_url" in data and data["image_url"]
            image_status = f"Image URL: {data.get('image_url', 'None')}"
            
            self.log_test("Specific Recipe", True, 
                f"Recipe loaded: {data.get('recipe_name')} from {data.get('origin_country')}. {image_status}")
            return True
            
        except Exception as e:
            self.log_test("Specific Recipe", False, f"Exception: {str(e)}")
            return False
            
    def test_recipe_search(self):
        """Test 5: Recipe Search - GET /api/recipes/search?q=carbonara"""
        print("\n=== Test 5: Recipe Search ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search?q=carbonara")
            
            if response.status_code != 200:
                self.log_test("Recipe Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Recipe Search", False, "Invalid JSON response")
                return False
                
            # Check response structure
            if "found" not in data:
                self.log_test("Recipe Search", False, "Missing 'found' field in response")
                return False
                
            if data.get("found"):
                if "recipes" not in data:
                    self.log_test("Recipe Search", False, "Found=true but missing 'recipes' field")
                    return False
                    
                recipes = data["recipes"]
                if not isinstance(recipes, list):
                    self.log_test("Recipe Search", False, "'recipes' is not a list")
                    return False
                    
                self.log_test("Recipe Search", True, 
                    f"Search successful: found {len(recipes)} recipes matching 'carbonara'")
            else:
                # No results is also valid
                self.log_test("Recipe Search", True, 
                    f"Search completed: no recipes found for 'carbonara'")
                
            return True
            
        except Exception as e:
            self.log_test("Recipe Search", False, f"Exception: {str(e)}")
            return False
            
    def test_continents_endpoint(self):
        """Test 6: Continents - GET /api/continents"""
        print("\n=== Test 6: Continents Endpoint ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/continents")
            
            if response.status_code != 200:
                self.log_test("Continents Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Continents Endpoint", False, "Invalid JSON response")
                return False
                
            if "continents" not in data:
                self.log_test("Continents Endpoint", False, "Missing 'continents' field in response")
                return False
                
            continents = data["continents"]
            
            if not isinstance(continents, list):
                self.log_test("Continents Endpoint", False, "'continents' is not a list")
                return False
                
            if len(continents) == 0:
                self.log_test("Continents Endpoint", False, "No continents returned")
                return False
                
            # Check continent structure
            first_continent = continents[0]
            required_fields = ["name", "slug"]
            missing_fields = [field for field in required_fields if field not in first_continent]
            
            if missing_fields:
                self.log_test("Continents Endpoint", False, f"Missing required fields: {missing_fields}")
                return False
                
            continent_names = [c.get("name") for c in continents]
            self.log_test("Continents Endpoint", True, 
                f"Returned {len(continents)} continents: {', '.join(continent_names)}")
            return True
            
        except Exception as e:
            self.log_test("Continents Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_countries_endpoint(self):
        """Test 7: Countries - GET /api/countries"""
        print("\n=== Test 7: Countries Endpoint ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/countries")
            
            if response.status_code != 200:
                self.log_test("Countries Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Countries Endpoint", False, "Invalid JSON response")
                return False
                
            if "countries" not in data:
                self.log_test("Countries Endpoint", False, "Missing 'countries' field in response")
                return False
                
            countries = data["countries"]
            
            if not isinstance(countries, list):
                self.log_test("Countries Endpoint", False, "'countries' is not a list")
                return False
                
            if len(countries) == 0:
                self.log_test("Countries Endpoint", False, "No countries returned")
                return False
                
            # Check country structure
            first_country = countries[0]
            required_fields = ["canonical", "name", "slug"]
            missing_fields = [field for field in required_fields if field not in first_country]
            
            if missing_fields:
                self.log_test("Countries Endpoint", False, f"Missing required fields: {missing_fields}")
                return False
                
            self.log_test("Countries Endpoint", True, 
                f"Returned {len(countries)} countries with proper structure")
            return True
            
        except Exception as e:
            self.log_test("Countries Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_recipes_by_continent(self):
        """Test 8: Recipes by Continent - GET /api/recipes/by-continent/europe"""
        print("\n=== Test 8: Recipes by Continent (Europe) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/by-continent/europe")
            
            if response.status_code != 200:
                self.log_test("Recipes by Continent", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Recipes by Continent", False, "Invalid JSON response")
                return False
                
            if "continent" not in data or "recipes" not in data:
                self.log_test("Recipes by Continent", False, "Missing required fields (continent, recipes)")
                return False
                
            recipes = data["recipes"]
            
            if not isinstance(recipes, list):
                self.log_test("Recipes by Continent", False, "'recipes' is not a list")
                return False
                
            continent_name = data.get("continent")
            
            self.log_test("Recipes by Continent", True, 
                f"Returned {len(recipes)} recipes from {continent_name}")
            return True
            
        except Exception as e:
            self.log_test("Recipes by Continent", False, f"Exception: {str(e)}")
            return False
            
    def test_recipes_by_country(self):
        """Test 9: Recipes by Country - GET /api/recipes/by-country/italy"""
        print("\n=== Test 9: Recipes by Country (Italy) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/by-country/italy")
            
            if response.status_code != 200:
                self.log_test("Recipes by Country", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Recipes by Country", False, "Invalid JSON response")
                return False
                
            required_fields = ["country", "recipes", "continent"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Recipes by Country", False, f"Missing required fields: {missing_fields}")
                return False
                
            recipes = data["recipes"]
            
            if not isinstance(recipes, list):
                self.log_test("Recipes by Country", False, "'recipes' is not a list")
                return False
                
            country_name = data.get("country")
            continent_name = data.get("continent")
            
            self.log_test("Recipes by Country", True, 
                f"Returned {len(recipes)} recipes from {country_name} ({continent_name})")
            return True
            
        except Exception as e:
            self.log_test("Recipes by Country", False, f"Exception: {str(e)}")
            return False
            
    def test_auth_me_endpoint(self):
        """Test 10: Auth Me - GET /api/auth/me (should return 401)"""
        print("\n=== Test 10: Auth Me Endpoint (Unauthorized) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/auth/me")
            
            if response.status_code != 401:
                self.log_test("Auth Me Unauthorized", False, 
                    f"Expected 401, got HTTP {response.status_code}: {response.text}")
                return False
                
            # Try to parse JSON response even for 401
            try:
                data = response.json()
                self.log_test("Auth Me Unauthorized", True, 
                    f"Correctly returned 401: {data.get('detail', 'Unauthorized')}")
            except json.JSONDecodeError:
                self.log_test("Auth Me Unauthorized", True, 
                    "Correctly returned 401 (non-JSON response)")
                
            return True
            
        except Exception as e:
            self.log_test("Auth Me Unauthorized", False, f"Exception: {str(e)}")
            return False
            
    def test_auth_login_endpoint(self):
        """Test 11: Auth Login - POST /api/auth/login (check endpoint exists)"""
        print("\n=== Test 11: Auth Login Endpoint (Existence Check) ===")
        
        try:
            # Send a POST request with invalid credentials to check if endpoint exists
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "email": "test@example.com",
                "password": "invalid"
            })
            
            # We expect either 401 (invalid credentials) or 400 (validation error)
            # Both indicate the endpoint exists and is processing requests
            if response.status_code in [400, 401, 422]:  # 422 is validation error
                try:
                    data = response.json()
                    self.log_test("Auth Login Endpoint", True, 
                        f"Endpoint exists - HTTP {response.status_code}: {data.get('detail', 'Validation/Auth error')}")
                except json.JSONDecodeError:
                    self.log_test("Auth Login Endpoint", True, 
                        f"Endpoint exists - HTTP {response.status_code}")
                return True
            elif response.status_code == 404:
                self.log_test("Auth Login Endpoint", False, "Login endpoint not found (404)")
                return False
            elif response.status_code == 405:
                self.log_test("Auth Login Endpoint", False, "Method not allowed (405)")
                return False
            else:
                self.log_test("Auth Login Endpoint", False, 
                    f"Unexpected response: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Auth Login Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_recipe_reviews(self):
        """Test 12: Recipe Reviews - GET /api/recipes/spaghetti-alla-carbonara-italy/reviews"""
        print("\n=== Test 12: Recipe Reviews ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/spaghetti-alla-carbonara-italy/reviews")
            
            if response.status_code == 404:
                self.log_test("Recipe Reviews", False, "Recipe not found for reviews (404) - may need to be seeded")
                return False
            elif response.status_code != 200:
                self.log_test("Recipe Reviews", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log_test("Recipe Reviews", False, "Invalid JSON response")
                return False
                
            # Check response structure
            required_fields = ["reviews", "total", "average_rating", "ratings_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Recipe Reviews", False, f"Missing required fields: {missing_fields}")
                return False
                
            reviews = data["reviews"]
            total = data["total"]
            avg_rating = data["average_rating"]
            ratings_count = data["ratings_count"]
            
            if not isinstance(reviews, list):
                self.log_test("Recipe Reviews", False, "'reviews' is not a list")
                return False
                
            self.log_test("Recipe Reviews", True, 
                f"Reviews loaded: {len(reviews)} reviews shown, {total} total, avg rating: {avg_rating}")
            return True
            
        except Exception as e:
            self.log_test("Recipe Reviews", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all comprehensive backend API tests"""
        print("🧪 Starting Comprehensive Backend API Tests for Sous Chef Linguine")
        print("Testing all major endpoints as specified in review request")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Run all test methods
        test_methods = [
            self.test_health_check,
            self.test_top_worldwide_recipes,
            self.test_featured_recipes,
            self.test_specific_recipe,
            self.test_recipe_search,
            self.test_continents_endpoint,
            self.test_countries_endpoint,
            self.test_recipes_by_continent,
            self.test_recipes_by_country,
            self.test_auth_me_endpoint,
            self.test_auth_login_endpoint,
            self.test_recipe_reviews
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
                self.log_test(test_name, False, f"Test method exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE BACKEND API TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
            
        # Critical Issues Summary
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ ISSUES FOUND:")
            for failed in failed_tests:
                print(f"  - {failed['test']}: {failed['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED - Backend API is functioning correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = SousChefBackendTester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    failed_tests = [r for r in results if not r["success"]]
    if failed_tests:
        print(f"\n❌ {len(failed_tests)} test(s) failed!")
        return 1
    else:
        print(f"\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())