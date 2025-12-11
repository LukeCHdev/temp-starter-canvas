#!/usr/bin/env python3
"""
Backend Test Suite for Sous Chef Linguine Recipe Search and Translation System
Tests the recipe search functionality with translation capabilities.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://linguine-chef.preview.emergentagent.com/api"

class SousChefTester:
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
        
    def test_search_existing_recipe_english(self):
        """Test Case 1: Search for existing recipe in English"""
        print("\n=== Test 1: Search for existing recipe in English ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Search Carbonara (EN)", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Check expected fields
            expected_fields = ["found", "generated", "translated", "recipe"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log_test("Search Carbonara (EN)", False, f"Missing fields: {missing_fields}", data)
                return None
                
            # Validate expected values
            if not data.get("found"):
                self.log_test("Search Carbonara (EN)", False, "Expected found=true", data)
                return None
                
            if data.get("generated"):
                self.log_test("Search Carbonara (EN)", False, "Expected generated=false", data)
                return None
                
            if data.get("translated"):
                self.log_test("Search Carbonara (EN)", False, "Expected translated=false", data)
                return None
                
            recipe = data.get("recipe")
            if not recipe or not recipe.get("slug"):
                self.log_test("Search Carbonara (EN)", False, "Recipe or slug missing", data)
                return None
                
            self.log_test("Search Carbonara (EN)", True, f"Found recipe with slug: {recipe['slug']}", data)
            return recipe
            
        except Exception as e:
            self.log_test("Search Carbonara (EN)", False, f"Exception: {str(e)}")
            return None
            
    def test_search_same_recipe_italian(self, english_recipe_slug: str = None):
        """Test Case 2: Search for SAME recipe in Italian (should translate, NOT create duplicate)"""
        print("\n=== Test 2: Search for same recipe in Italian ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "it"
            })
            
            if response.status_code != 200:
                self.log_test("Search Carbonara (IT)", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Check expected fields
            expected_fields = ["found", "generated", "translated", "recipe"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log_test("Search Carbonara (IT)", False, f"Missing fields: {missing_fields}", data)
                return None
                
            # Validate expected values
            if not data.get("found"):
                self.log_test("Search Carbonara (IT)", False, "Expected found=true", data)
                return None
                
            if data.get("generated"):
                self.log_test("Search Carbonara (IT)", False, "Expected generated=false", data)
                return None
                
            if not data.get("translated"):
                self.log_test("Search Carbonara (IT)", False, "Expected translated=true (IMPORTANT!)", data)
                return None
                
            recipe = data.get("recipe")
            if not recipe or not recipe.get("slug"):
                self.log_test("Search Carbonara (IT)", False, "Recipe or slug missing", data)
                return None
                
            # Check if same slug as English version
            if english_recipe_slug and recipe["slug"] != english_recipe_slug:
                self.log_test("Search Carbonara (IT)", False, f"Different slug! EN: {english_recipe_slug}, IT: {recipe['slug']}", data)
                return None
                
            # Check if history_summary is in Italian (basic check)
            history = recipe.get("history_summary", "")
            if not history:
                self.log_test("Search Carbonara (IT)", False, "No history_summary found", data)
                return None
                
            self.log_test("Search Carbonara (IT)", True, f"Translated recipe with same slug: {recipe['slug']}", data)
            return recipe
            
        except Exception as e:
            self.log_test("Search Carbonara (IT)", False, f"Exception: {str(e)}")
            return None
            
    def test_search_new_recipe_english(self):
        """Test Case 3: Search for new recipe in English"""
        print("\n=== Test 3: Search for new recipe in English ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Kimchi Jjigae",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Search Kimchi Jjigae (EN)", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            
            # Check expected fields
            expected_fields = ["found", "generated", "translated", "recipe"]
            missing_fields = [field for field in expected_fields if field not in data]
            
            if missing_fields:
                self.log_test("Search Kimchi Jjigae (EN)", False, f"Missing fields: {missing_fields}", data)
                return None
                
            # For new recipe, it should be generated
            if not data.get("generated"):
                self.log_test("Search Kimchi Jjigae (EN)", False, "Expected generated=true", data)
                return None
                
            recipe = data.get("recipe")
            if not recipe or not recipe.get("slug"):
                self.log_test("Search Kimchi Jjigae (EN)", False, "Recipe or slug missing", data)
                return None
                
            # Check if technique_links field exists
            if "technique_links" not in recipe:
                self.log_test("Search Kimchi Jjigae (EN)", False, "technique_links field missing", data)
                return None
                
            self.log_test("Search Kimchi Jjigae (EN)", True, f"Generated recipe with slug: {recipe['slug']}, technique_links present", data)
            return recipe
            
        except Exception as e:
            self.log_test("Search Kimchi Jjigae (EN)", False, f"Exception: {str(e)}")
            return None
            
    def test_verify_no_duplicates(self):
        """Test Case 4: Verify no duplicates were created"""
        print("\n=== Test 4: Verify no duplicates were created ===")
        
        try:
            # Search for recipes with similar names
            test_queries = ["Carbonara", "Spaghetti Carbonara", "Pasta Carbonara"]
            found_slugs = set()
            
            for query in test_queries:
                response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                    "q": query,
                    "lang": "en"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("recipe") and data["recipe"].get("slug"):
                        found_slugs.add(data["recipe"]["slug"])
            
            # Check if we found multiple different slugs for similar recipes
            if len(found_slugs) > 1:
                self.log_test("No Duplicates Check", False, f"Found multiple slugs for similar recipes: {list(found_slugs)}")
                return False
            elif len(found_slugs) == 1:
                self.log_test("No Duplicates Check", True, f"Single slug found for Carbonara variants: {list(found_slugs)[0]}")
                return True
            else:
                self.log_test("No Duplicates Check", False, "No recipes found for Carbonara variants")
                return False
                
        except Exception as e:
            self.log_test("No Duplicates Check", False, f"Exception: {str(e)}")
            return False
            
    def test_technique_links_field(self):
        """Test Case 5: Test the technique_links field structure"""
        print("\n=== Test 5: Test technique_links field structure ===")
        
        try:
            # Get a recipe that should have technique_links
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Technique Links Field", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            recipe = data.get("recipe")
            
            if not recipe:
                self.log_test("Technique Links Field", False, "No recipe found")
                return False
                
            # Check if technique_links field exists
            if "technique_links" not in recipe:
                self.log_test("Technique Links Field", False, "technique_links field missing from recipe")
                return False
                
            technique_links = recipe["technique_links"]
            
            # Should be an array (even if empty)
            if not isinstance(technique_links, list):
                self.log_test("Technique Links Field", False, f"technique_links should be array, got: {type(technique_links)}")
                return False
                
            # If not empty, check structure
            if technique_links:
                for i, link in enumerate(technique_links):
                    required_fields = ["technique", "url", "description"]
                    missing = [field for field in required_fields if field not in link]
                    if missing:
                        self.log_test("Technique Links Field", False, f"technique_links[{i}] missing fields: {missing}")
                        return False
                        
            self.log_test("Technique Links Field", True, f"technique_links field valid (array with {len(technique_links)} items)")
            return True
            
        except Exception as e:
            self.log_test("Technique Links Field", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Starting Sous Chef Linguine Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Test 1: Search existing recipe in English
        english_recipe = self.test_search_existing_recipe_english()
        english_slug = english_recipe["slug"] if english_recipe else None
        
        # Test 2: Search same recipe in Italian
        self.test_search_same_recipe_italian(english_slug)
        
        # Test 3: Search new recipe in English
        self.test_search_new_recipe_english()
        
        # Test 4: Verify no duplicates
        self.test_verify_no_duplicates()
        
        # Test 5: Test technique_links field
        self.test_technique_links_field()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
            
        return self.test_results

def main():
    """Main test runner"""
    tester = SousChefTester()
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