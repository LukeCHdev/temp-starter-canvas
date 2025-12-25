#!/usr/bin/env python3
"""
Translation and Technique Links Test Suite for Sous Chef Linguine
Tests language translation functionality and technique_links field as per review request.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://seoboost-9.preview.emergentagent.com/api"

class TranslationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.initial_recipe_count = None
        
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
        
    def get_admin_stats(self):
        """Get admin stats to check recipe count"""
        try:
            # First login to get admin token
            login_response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": "SousChefAdmin2024!"
            })
            
            if login_response.status_code != 200:
                return None
                
            token = login_response.json().get("token")
            if not token:
                return None
                
            # Get stats
            headers = {"Authorization": f"Bearer {token}"}
            stats_response = self.session.get(f"{BACKEND_URL}/admin/stats", headers=headers)
            
            if stats_response.status_code == 200:
                return stats_response.json()
            return None
            
        except Exception as e:
            print(f"Error getting admin stats: {str(e)}")
            return None
    
    def test_carbonara_english(self):
        """Test Case 1: Search Carbonara with lang=en (should return translated: false)"""
        print("\n=== Test 1: Carbonara Search (English) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Carbonara English Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields
            if "found" not in data or "generated" not in data or "translated" not in data or "recipe" not in data:
                self.log_test("Carbonara English Search", False, f"Missing required fields in response: {list(data.keys())}")
                return False
            
            # Should return translated: false for English
            if data.get("translated") != False:
                self.log_test("Carbonara English Search", False, f"Expected translated: false, got {data.get('translated')}")
                return False
                
            recipe = data.get("recipe", {})
            slug = recipe.get("slug")
            
            if not slug:
                self.log_test("Carbonara English Search", False, "No slug returned in recipe")
                return False
                
            # Store slug for comparison in other tests
            self.carbonara_slug = slug
            
            self.log_test("Carbonara English Search", True, f"Found recipe with slug: {slug}, translated: false")
            return True
            
        except Exception as e:
            self.log_test("Carbonara English Search", False, f"Exception: {str(e)}")
            return False
    
    def test_carbonara_italian(self):
        """Test Case 2: Search Carbonara with lang=it (should return translated: true, _display_lang: "it")"""
        print("\n=== Test 2: Carbonara Search (Italian) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "it"
            })
            
            if response.status_code != 200:
                self.log_test("Carbonara Italian Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields
            if "found" not in data or "generated" not in data or "translated" not in data or "recipe" not in data:
                self.log_test("Carbonara Italian Search", False, f"Missing required fields in response: {list(data.keys())}")
                return False
            
            # Should return translated: true for Italian
            if data.get("translated") != True:
                self.log_test("Carbonara Italian Search", False, f"Expected translated: true, got {data.get('translated')}")
                return False
                
            recipe = data.get("recipe", {})
            slug = recipe.get("slug")
            
            # Should be same slug as English version
            if hasattr(self, 'carbonara_slug') and slug != self.carbonara_slug:
                self.log_test("Carbonara Italian Search", False, f"Slug mismatch: expected {self.carbonara_slug}, got {slug}")
                return False
                
            # Check translation metadata
            display_lang = recipe.get("_display_lang")
            if display_lang != "it":
                self.log_test("Carbonara Italian Search", False, f"Expected _display_lang: 'it', got {display_lang}")
                return False
                
            self.log_test("Carbonara Italian Search", True, f"Recipe translated to Italian, same slug: {slug}, _display_lang: it")
            return True
            
        except Exception as e:
            self.log_test("Carbonara Italian Search", False, f"Exception: {str(e)}")
            return False
    
    def test_carbonara_french(self):
        """Test Case 3: Search Carbonara with lang=fr (should return translated: true, _display_lang: "fr")"""
        print("\n=== Test 3: Carbonara Search (French) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "fr"
            })
            
            if response.status_code != 200:
                self.log_test("Carbonara French Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Should return translated: true for French
            if data.get("translated") != True:
                self.log_test("Carbonara French Search", False, f"Expected translated: true, got {data.get('translated')}")
                return False
                
            recipe = data.get("recipe", {})
            slug = recipe.get("slug")
            
            # Should be same slug as English version
            if hasattr(self, 'carbonara_slug') and slug != self.carbonara_slug:
                self.log_test("Carbonara French Search", False, f"Slug mismatch: expected {self.carbonara_slug}, got {slug}")
                return False
                
            # Check translation metadata
            display_lang = recipe.get("_display_lang")
            if display_lang != "fr":
                self.log_test("Carbonara French Search", False, f"Expected _display_lang: 'fr', got {display_lang}")
                return False
                
            self.log_test("Carbonara French Search", True, f"Recipe translated to French, same slug: {slug}, _display_lang: fr")
            return True
            
        except Exception as e:
            self.log_test("Carbonara French Search", False, f"Exception: {str(e)}")
            return False
    
    def test_carbonara_german(self):
        """Test Case 4: Search Carbonara with lang=de (should return translated: true, _display_lang: "de")"""
        print("\n=== Test 4: Carbonara Search (German) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "de"
            })
            
            if response.status_code != 200:
                self.log_test("Carbonara German Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Should return translated: true for German
            if data.get("translated") != True:
                self.log_test("Carbonara German Search", False, f"Expected translated: true, got {data.get('translated')}")
                return False
                
            recipe = data.get("recipe", {})
            slug = recipe.get("slug")
            
            # Should be same slug as English version
            if hasattr(self, 'carbonara_slug') and slug != self.carbonara_slug:
                self.log_test("Carbonara German Search", False, f"Slug mismatch: expected {self.carbonara_slug}, got {slug}")
                return False
                
            # Check translation metadata
            display_lang = recipe.get("_display_lang")
            if display_lang != "de":
                self.log_test("Carbonara German Search", False, f"Expected _display_lang: 'de', got {display_lang}")
                return False
                
            self.log_test("Carbonara German Search", True, f"Recipe translated to German, same slug: {slug}, _display_lang: de")
            return True
            
        except Exception as e:
            self.log_test("Carbonara German Search", False, f"Exception: {str(e)}")
            return False
    
    def test_no_duplicate_creation(self):
        """Test Case 5: Verify no duplicates created during translation tests"""
        print("\n=== Test 5: No Duplicate Creation Check ===")
        
        try:
            final_stats = self.get_admin_stats()
            
            if not final_stats:
                self.log_test("No Duplicate Creation", False, "Could not retrieve final admin stats")
                return False
                
            final_count = final_stats.get("total_recipes", 0)
            
            if self.initial_recipe_count is None:
                self.log_test("No Duplicate Creation", False, "Initial recipe count not available")
                return False
                
            if final_count != self.initial_recipe_count:
                self.log_test("No Duplicate Creation", False, f"Recipe count changed: {self.initial_recipe_count} -> {final_count}")
                return False
                
            self.log_test("No Duplicate Creation", True, f"Recipe count unchanged: {final_count} recipes")
            return True
            
        except Exception as e:
            self.log_test("No Duplicate Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_technique_links_kimchi(self):
        """Test Case 6: Search for recipe with technique_links (Kimchi)"""
        print("\n=== Test 6: Technique Links Test (Kimchi) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Kimchi",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Technique Links Kimchi", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            recipe = data.get("recipe", {})
            
            # Check if technique_links field exists
            technique_links = recipe.get("technique_links")
            
            if technique_links is None:
                self.log_test("Technique Links Kimchi", False, "technique_links field missing from recipe")
                return False
                
            if not isinstance(technique_links, list):
                self.log_test("Technique Links Kimchi", False, f"technique_links should be array, got {type(technique_links)}")
                return False
                
            # If technique_links exists and is array, check structure
            if technique_links:
                for i, link in enumerate(technique_links):
                    if not isinstance(link, dict):
                        self.log_test("Technique Links Kimchi", False, f"technique_links[{i}] should be object, got {type(link)}")
                        return False
                        
                    required_fields = ["technique", "url", "description"]
                    missing_fields = [field for field in required_fields if field not in link]
                    
                    if missing_fields:
                        self.log_test("Technique Links Kimchi", False, f"technique_links[{i}] missing fields: {missing_fields}")
                        return False
                        
                self.log_test("Technique Links Kimchi", True, f"technique_links field present with {len(technique_links)} links")
            else:
                self.log_test("Technique Links Kimchi", True, "technique_links field present (empty array)")
                
            return True
            
        except Exception as e:
            self.log_test("Technique Links Kimchi", False, f"Exception: {str(e)}")
            return False
    
    def test_technique_links_pasta(self):
        """Test Case 7: Search for recipe with technique_links (Pasta e patate)"""
        print("\n=== Test 7: Technique Links Test (Pasta e patate) ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Pasta e patate",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("Technique Links Pasta", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            recipe = data.get("recipe", {})
            
            # Check if technique_links field exists
            technique_links = recipe.get("technique_links")
            
            if technique_links is None:
                self.log_test("Technique Links Pasta", False, "technique_links field missing from recipe")
                return False
                
            if not isinstance(technique_links, list):
                self.log_test("Technique Links Pasta", False, f"technique_links should be array, got {type(technique_links)}")
                return False
                
            # If technique_links exists and is array, check structure
            if technique_links:
                for i, link in enumerate(technique_links):
                    if not isinstance(link, dict):
                        self.log_test("Technique Links Pasta", False, f"technique_links[{i}] should be object, got {type(link)}")
                        return False
                        
                    required_fields = ["technique", "url", "description"]
                    missing_fields = [field for field in required_fields if field not in link]
                    
                    if missing_fields:
                        self.log_test("Technique Links Pasta", False, f"technique_links[{i}] missing fields: {missing_fields}")
                        return False
                        
                self.log_test("Technique Links Pasta", True, f"technique_links field present with {len(technique_links)} links")
            else:
                self.log_test("Technique Links Pasta", True, "technique_links field present (empty array)")
                
            return True
            
        except Exception as e:
            self.log_test("Technique Links Pasta", False, f"Exception: {str(e)}")
            return False
    
    def test_api_format_validation(self):
        """Test Case 8: Validate API response format"""
        print("\n=== Test 8: API Format Validation ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("API Format Validation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check top-level response format
            required_response_fields = ["found", "generated", "translated", "recipe"]
            missing_response_fields = [field for field in required_response_fields if field not in data]
            
            if missing_response_fields:
                self.log_test("API Format Validation", False, f"Missing response fields: {missing_response_fields}")
                return False
                
            recipe = data.get("recipe", {})
            
            # Check recipe format
            required_recipe_fields = ["slug", "content_language", "origin_language"]
            missing_recipe_fields = [field for field in required_recipe_fields if field not in recipe]
            
            if missing_recipe_fields:
                self.log_test("API Format Validation", False, f"Missing recipe fields: {missing_recipe_fields}")
                return False
                
            # Check content_language is "en" for stored recipes
            content_language = recipe.get("content_language")
            if content_language != "en":
                self.log_test("API Format Validation", False, f"Expected content_language: 'en', got '{content_language}'")
                return False
                
            self.log_test("API Format Validation", True, "API response format is correct")
            return True
            
        except Exception as e:
            self.log_test("API Format Validation", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all translation and technique_links tests as per review request"""
        print("🧪 Starting Sous Chef Linguine Translation & Technique Links Tests")
        print("Testing language translation and technique_links functionality")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Get initial recipe count
        initial_stats = self.get_admin_stats()
        if initial_stats:
            self.initial_recipe_count = initial_stats.get("total_recipes", 0)
            print(f"Initial recipe count: {self.initial_recipe_count}")
        
        # Test 1: Carbonara English (translated: false)
        self.test_carbonara_english()
        
        # Test 2: Carbonara Italian (translated: true, _display_lang: "it")
        self.test_carbonara_italian()
        
        # Test 3: Carbonara French (translated: true, _display_lang: "fr")
        self.test_carbonara_french()
        
        # Test 4: Carbonara German (translated: true, _display_lang: "de")
        self.test_carbonara_german()
        
        # Test 5: No duplicate creation
        self.test_no_duplicate_creation()
        
        # Test 6: Technique links - Kimchi
        self.test_technique_links_kimchi()
        
        # Test 7: Technique links - Pasta e patate
        self.test_technique_links_pasta()
        
        # Test 8: API format validation
        self.test_api_format_validation()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
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
            print(f"\n❌ CRITICAL ISSUES FOUND:")
            for failed in failed_tests:
                print(f"  - {failed['test']}: {failed['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED - Translation & Technique Links working correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = TranslationTester()
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