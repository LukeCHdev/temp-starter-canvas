#!/usr/bin/env python3
"""
Backend Test Suite for Sous Chef Linguine Admin Panel APIs
Tests admin authentication, recipe management, and JSON import functionality.
"""

import requests
import json
import time
import base64
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://authentic-cuisine.preview.emergentagent.com/api"
ADMIN_PASSWORD = "SousChefAdmin2024!"

class AdminPanelTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        
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
        
    def test_admin_login_success(self):
        """Test Case 1: Admin Authentication - Valid Password"""
        print("\n=== Test 1: Admin Login with Valid Password ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code != 200:
                self.log_test("Admin Login (Valid)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if not data.get("success"):
                self.log_test("Admin Login (Valid)", False, f"Expected success=true, got {data.get('success')}")
                return False
                
            if not data.get("token"):
                self.log_test("Admin Login (Valid)", False, "No token returned")
                return False
                
            # Store token for subsequent tests
            self.admin_token = data["token"]
            
            self.log_test("Admin Login (Valid)", True, f"Login successful, token received")
            return True
            
        except Exception as e:
            self.log_test("Admin Login (Valid)", False, f"Exception: {str(e)}")
            return False
            
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
            
    def test_translation_duplicate_prevention(self):
        """Test Case 3: Translation Test - Same recipe in different languages should return same slug"""
        print("\n=== Test 3: Translation Duplicate Prevention ===")
        
        try:
            # Use Beef Wellington (English recipe) for translation test
            # First get English version
            response_en = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Beef Wellington",
                "lang": "en"
            })
            
            if response_en.status_code != 200:
                self.log_test("Translation Test (EN)", False, f"HTTP {response_en.status_code}: {response_en.text}")
                return False
                
            data_en = response_en.json()
            recipe_en = data_en.get("recipe")
            
            if not recipe_en or not recipe_en.get("slug"):
                self.log_test("Translation Test (EN)", False, "No English recipe found")
                return False
                
            english_slug = recipe_en["slug"]
            english_origin_lang = recipe_en.get("origin_language", "en")
            
            # Now get Italian version (should be translated)
            response_it = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Beef Wellington", 
                "lang": "it"
            })
            
            if response_it.status_code != 200:
                self.log_test("Translation Test (IT)", False, f"HTTP {response_it.status_code}: {response_it.text}")
                return False
                
            data_it = response_it.json()
            
            # Check expected response structure
            if not data_it.get("found"):
                self.log_test("Translation Test (IT)", False, f"Expected found=true, got {data_it.get('found')}")
                return False
                
            if data_it.get("generated"):
                self.log_test("Translation Test (IT)", False, f"Expected generated=false (should reuse existing), got {data_it.get('generated')}")
                return False
                
            # Only expect translation if original language is different from requested language
            if english_origin_lang != "it":
                if not data_it.get("translated"):
                    self.log_test("Translation Test (IT)", False, f"Expected translated=true for English->Italian, got {data_it.get('translated')}")
                    return False
            
            recipe_it = data_it.get("recipe")
            if not recipe_it or not recipe_it.get("slug"):
                self.log_test("Translation Test (IT)", False, "No Italian recipe found")
                return False
                
            italian_slug = recipe_it["slug"]
            
            # Check if same slug
            if english_slug == italian_slug:
                self.log_test("Translation Duplicate Prevention", True, f"Same slug for both languages: {english_slug}, translated: {data_it.get('translated')}")
                return True
            else:
                self.log_test("Translation Duplicate Prevention", False, f"Different slugs! EN: {english_slug}, IT: {italian_slug}")
                return False
                
        except Exception as e:
            self.log_test("Translation Duplicate Prevention", False, f"Exception: {str(e)}")
            return False
            
    def test_api_endpoint_format(self):
        """Test Case 4: API Endpoint Format Validation"""
        print("\n=== Test 4: API Endpoint Format Validation ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                "q": "Carbonara",
                "lang": "en"
            })
            
            if response.status_code != 200:
                self.log_test("API Format Test", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required top-level fields
            required_fields = ["found", "generated", "translated", "recipe"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("API Format Test", False, f"Missing top-level fields: {missing_fields}")
                return False
                
            recipe = data.get("recipe")
            if not recipe:
                self.log_test("API Format Test", False, "No recipe object found")
                return False
                
            # Check required recipe fields
            required_recipe_fields = ["recipe_name", "slug", "origin_country", "origin_region"]
            missing_recipe_fields = [field for field in required_recipe_fields if field not in recipe]
            
            if missing_recipe_fields:
                self.log_test("API Format Test", False, f"Missing recipe fields: {missing_recipe_fields}")
                return False
                
            self.log_test("API Format Test", True, "All required fields present in API response")
            return True
            
        except Exception as e:
            self.log_test("API Format Test", False, f"Exception: {str(e)}")
            return False
            
    def test_comprehensive_duplicate_prevention(self):
        """Test Case 5: Comprehensive Duplicate Prevention Test"""
        print("\n=== Test 5: Comprehensive Duplicate Prevention ===")
        
        # Test multiple variations of the same dish
        test_groups = [
            {
                "dish": "Carbonara",
                "variations": ["Carbonara", "Spaghetti Carbonara", "Pasta Carbonara", "carbonara", "Spaghetti alla Carbonara"]
            },
            {
                "dish": "Wellington", 
                "variations": ["Beef Wellington", "Wellington"]
            }
        ]
        
        all_passed = True
        
        for group in test_groups:
            print(f"\n  Testing {group['dish']} variations:")
            found_slugs = set()
            
            for variation in group["variations"]:
                try:
                    response = self.session.get(f"{BACKEND_URL}/recipes/search", params={
                        "q": variation,
                        "lang": "en"
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("recipe") and data["recipe"].get("slug"):
                            slug = data["recipe"]["slug"]
                            found_slugs.add(slug)
                            print(f"    '{variation}' -> {slug}")
                            
                except Exception as e:
                    print(f"    '{variation}' -> ERROR: {str(e)}")
                    all_passed = False
            
            # Check if all variations returned the same slug
            if len(found_slugs) <= 1:
                dish_name = group["dish"]
                if found_slugs:
                    slug = list(found_slugs)[0]
                    self.log_test(f"Duplicate Prevention ({dish_name})", True, f"All {dish_name} variations return same slug: {slug}")
                else:
                    self.log_test(f"Duplicate Prevention ({dish_name})", False, f"No recipes found for {dish_name} variations")
                    all_passed = False
            else:
                self.log_test(f"Duplicate Prevention ({dish_name})", False, f"Found {len(found_slugs)} different slugs for {dish_name}: {list(found_slugs)}")
                all_passed = False
                
        return all_passed
            
    def run_all_tests(self):
        """Run all test cases based on review request"""
        print("🧪 Starting Sous Chef Linguine Recipe Search API Tests")
        print("Testing duplicate prevention and country attribution fixes")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Test 1: Duplicate Prevention Tests
        self.test_duplicate_prevention_carbonara()
        
        # Test 2: Country Attribution Tests  
        self.test_country_attribution_fixes()
        
        # Test 3: Translation Test (Duplicate Prevention across languages)
        self.test_translation_duplicate_prevention()
        
        # Test 4: API Endpoint Format
        self.test_api_endpoint_format()
        
        # Test 5: Comprehensive Duplicate Prevention
        self.test_comprehensive_duplicate_prevention()
        
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
            print(f"\n✅ ALL TESTS PASSED - Duplicate prevention and country attribution working correctly!")
            
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