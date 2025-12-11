#!/usr/bin/env python3
"""
Backend Test Suite for Sous Chef Linguine Recipe Search API
Tests duplicate prevention and country attribution fixes as per review request.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://authentic-cuisine.preview.emergentagent.com/api"

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
        
    def test_duplicate_prevention_carbonara(self):
        """Test Case 1: Duplicate Prevention - All Carbonara variations should return same recipe"""
        print("\n=== Test 1: Duplicate Prevention - Carbonara Variations ===")
        
        carbonara_queries = [
            "Carbonara",
            "Spaghetti Carbonara", 
            "Pasta Carbonara",
            "carbonara"  # lowercase test
        ]
        
        found_recipes = {}
        all_passed = True
        
        for query in carbonara_queries:
            try:
                response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                    "q": query,
                    "lang": "en"
                })
                
                if response.status_code != 200:
                    self.log_test(f"Carbonara Duplicate Test ({query})", False, f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue
                    
                data = response.json()
                
                # Check expected response structure
                if not data.get("found"):
                    self.log_test(f"Carbonara Duplicate Test ({query})", False, f"Expected found=true, got {data.get('found')}")
                    all_passed = False
                    continue
                    
                if data.get("generated"):
                    self.log_test(f"Carbonara Duplicate Test ({query})", False, f"Expected generated=false (should find existing), got {data.get('generated')}")
                    all_passed = False
                    continue
                
                recipe = data.get("recipe")
                if not recipe or not recipe.get("slug"):
                    self.log_test(f"Carbonara Duplicate Test ({query})", False, "Recipe or slug missing")
                    all_passed = False
                    continue
                    
                found_recipes[query] = recipe["slug"]
                print(f"  Query '{query}' -> slug: {recipe['slug']}")
                
            except Exception as e:
                self.log_test(f"Carbonara Duplicate Test ({query})", False, f"Exception: {str(e)}")
                all_passed = False
        
        # Check if all queries returned the same slug
        unique_slugs = set(found_recipes.values())
        if len(unique_slugs) == 1:
            slug = list(unique_slugs)[0]
            self.log_test("Carbonara Duplicate Prevention", True, f"All Carbonara variations return same recipe: {slug}")
        else:
            self.log_test("Carbonara Duplicate Prevention", False, f"Found {len(unique_slugs)} different slugs: {list(unique_slugs)}")
            all_passed = False
            
        return all_passed and len(found_recipes) > 0
            
    def test_country_attribution_fixes(self):
        """Test Case 2: Country Attribution - Verify correct country origins"""
        print("\n=== Test 2: Country Attribution Tests ===")
        
        test_cases = [
            {
                "query": "Peking Duck",
                "expected_country": "China",
                "description": "Chinese dish should not default to Italy"
            },
            {
                "query": "Beef Wellington", 
                "expected_country": "United Kingdom",
                "description": "British dish should not default to Italy"
            },
            {
                "query": "Kimchi",
                "expected_country": "South Korea", 
                "description": "Korean dish should not default to Italy"
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                    "q": test_case["query"],
                    "lang": "en"
                })
                
                if response.status_code != 200:
                    self.log_test(f"Country Attribution ({test_case['query']})", False, f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue
                    
                data = response.json()
                recipe = data.get("recipe")
                
                if not recipe:
                    self.log_test(f"Country Attribution ({test_case['query']})", False, "No recipe returned")
                    all_passed = False
                    continue
                
                actual_country = recipe.get("origin_country")
                expected_country = test_case["expected_country"]
                
                if actual_country == expected_country:
                    self.log_test(f"Country Attribution ({test_case['query']})", True, f"Correct country: {actual_country}")
                else:
                    self.log_test(f"Country Attribution ({test_case['query']})", False, f"Expected {expected_country}, got {actual_country}")
                    all_passed = False
                    
                print(f"  {test_case['query']} -> {actual_country} (expected: {expected_country})")
                
            except Exception as e:
                self.log_test(f"Country Attribution ({test_case['query']})", False, f"Exception: {str(e)}")
                all_passed = False
                
        return all_passed
            
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