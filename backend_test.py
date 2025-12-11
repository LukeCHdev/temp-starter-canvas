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
            
    def test_admin_login_failure(self):
        """Test Case 2: Admin Authentication - Invalid Password"""
        print("\n=== Test 2: Admin Login with Invalid Password ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": "wrongpassword"
            })
            
            if response.status_code == 401:
                self.log_test("Admin Login (Invalid)", True, "Correctly rejected invalid password with 401")
                return True
            else:
                self.log_test("Admin Login (Invalid)", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login (Invalid)", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_verify_token(self):
        """Test Case 3: Admin Token Verification"""
        print("\n=== Test 3: Admin Token Verification ===")
        
        if not self.admin_token:
            self.log_test("Admin Token Verify", False, "No admin token available from login test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/verify", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Token Verify", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if data.get("valid") == True:
                self.log_test("Admin Token Verify", True, "Token verification successful")
                return True
            else:
                self.log_test("Admin Token Verify", False, f"Expected valid=true, got {data.get('valid')}")
                return False
                
        except Exception as e:
            self.log_test("Admin Token Verify", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_recipes_list(self):
        """Test Case 4: Admin Recipe Management - Get All Recipes"""
        print("\n=== Test 4: Admin Get All Recipes ===")
        
        if not self.admin_token:
            self.log_test("Admin Recipes List", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/recipes", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Recipes List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if "recipes" not in data or "total" not in data:
                self.log_test("Admin Recipes List", False, "Missing 'recipes' or 'total' in response")
                return False
                
            recipes = data.get("recipes", [])
            total = data.get("total", 0)
            
            if len(recipes) != total:
                self.log_test("Admin Recipes List", False, f"Recipe count mismatch: got {len(recipes)}, expected {total}")
                return False
                
            self.log_test("Admin Recipes List", True, f"Retrieved {total} recipes successfully")
            return True
            
        except Exception as e:
            self.log_test("Admin Recipes List", False, f"Exception: {str(e)}")
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