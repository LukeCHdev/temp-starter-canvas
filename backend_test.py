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
BACKEND_URL = "https://global-recipes-23.preview.emergentagent.com/api"
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
            
    def test_admin_single_recipe(self):
        """Test Case 5: Admin Recipe Management - Get Single Recipe"""
        print("\n=== Test 5: Admin Get Single Recipe ===")
        
        if not self.admin_token:
            self.log_test("Admin Single Recipe", False, "No admin token available")
            return False
            
        try:
            # First get list of recipes to find a valid slug
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/recipes", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Single Recipe", False, f"Failed to get recipes list: {response.status_code}")
                return False
                
            data = response.json()
            recipes = data.get("recipes", [])
            
            if not recipes:
                self.log_test("Admin Single Recipe", False, "No recipes available to test")
                return False
                
            # Use first recipe's slug
            test_slug = recipes[0].get("slug")
            if not test_slug:
                self.log_test("Admin Single Recipe", False, "No slug found in first recipe")
                return False
                
            # Now test getting single recipe
            response = self.session.get(f"{BACKEND_URL}/admin/recipes/{test_slug}", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Single Recipe", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if "recipe" not in data:
                self.log_test("Admin Single Recipe", False, "Missing 'recipe' in response")
                return False
                
            recipe = data["recipe"]
            if recipe.get("slug") != test_slug:
                self.log_test("Admin Single Recipe", False, f"Slug mismatch: expected {test_slug}, got {recipe.get('slug')}")
                return False
                
            self.log_test("Admin Single Recipe", True, f"Retrieved recipe '{test_slug}' successfully")
            return True
            
        except Exception as e:
            self.log_test("Admin Single Recipe", False, f"Exception: {str(e)}")
            return False
    def test_admin_json_import(self):
        """Test Case 6: Admin JSON Import"""
        print("\n=== Test 6: Admin JSON Import ===")
        
        if not self.admin_token:
            self.log_test("Admin JSON Import", False, "No admin token available")
            return False
            
        # Test recipe JSON from review request
        test_recipe = {
            "recipe_name": "Test Admin Recipe",
            "origin_country": "France", 
            "origin_region": "Provence",
            "authenticity_level": 2,
            "history_summary": "A test recipe for admin panel",
            "characteristic_profile": "Test flavor profile",
            "no_no_rules": ["Test rule 1"],
            "special_techniques": ["Test technique"],
            "ingredients": [{"item": "Test ingredient", "amount": "100", "unit": "g", "notes": ""}],
            "instructions": ["Step 1", "Step 2"],
            "wine_pairing": {"recommended_wines": [], "notes": "Test notes"}
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BACKEND_URL}/admin/import/json", 
                                       headers=headers,
                                       json={"recipe_json": test_recipe})
            
            if response.status_code != 200:
                self.log_test("Admin JSON Import", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if not data.get("success"):
                self.log_test("Admin JSON Import", False, f"Import failed: {data}")
                return False
                
            if not data.get("slug"):
                self.log_test("Admin JSON Import", False, "No slug returned from import")
                return False
                
            imported_slug = data["slug"]
            self.log_test("Admin JSON Import", True, f"Recipe imported successfully with slug: {imported_slug}")
            
            # Test duplicate detection - try importing same recipe again
            response2 = self.session.post(f"{BACKEND_URL}/admin/import/json", 
                                        headers=headers,
                                        json={"recipe_json": test_recipe})
            
            if response2.status_code == 400:
                self.log_test("Admin JSON Duplicate Detection", True, "Correctly rejected duplicate recipe")
                return True
            else:
                self.log_test("Admin JSON Duplicate Detection", False, f"Expected 400 for duplicate, got {response2.status_code}")
                return False
            
        except Exception as e:
            self.log_test("Admin JSON Import", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_stats(self):
        """Test Case 7: Admin Dashboard Statistics"""
        print("\n=== Test 7: Admin Dashboard Statistics ===")
        
        if not self.admin_token:
            self.log_test("Admin Stats", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/stats", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Stats", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields
            required_fields = ["total_recipes", "published_recipes", "recipes_by_country", "recipes_by_continent", "recent_recipes"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Admin Stats", False, f"Missing fields: {missing_fields}")
                return False
                
            total_recipes = data.get("total_recipes", 0)
            published_recipes = data.get("published_recipes", 0)
            
            if total_recipes < 0 or published_recipes < 0:
                self.log_test("Admin Stats", False, f"Invalid recipe counts: total={total_recipes}, published={published_recipes}")
                return False
                
            self.log_test("Admin Stats", True, f"Stats retrieved: {total_recipes} total, {published_recipes} published")
            return True
            
        except Exception as e:
            self.log_test("Admin Stats", False, f"Exception: {str(e)}")
            return False
            
    def test_csv_template(self):
        """Test Case 8: CSV Template Endpoint"""
        print("\n=== Test 8: CSV Template ===")
        
        if not self.admin_token:
            self.log_test("CSV Template", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/csv-template", headers=headers)
            
            if response.status_code != 200:
                self.log_test("CSV Template", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if "headers" not in data or "notes" not in data:
                self.log_test("CSV Template", False, "Missing 'headers' or 'notes' in response")
                return False
                
            headers_list = data.get("headers", [])
            if not headers_list or len(headers_list) < 10:
                self.log_test("CSV Template", False, f"Invalid headers list: {len(headers_list)} items")
                return False
                
            self.log_test("CSV Template", True, f"CSV template retrieved with {len(headers_list)} headers")
            return True
            
        except Exception as e:
            self.log_test("CSV Template", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all admin panel test cases based on review request"""
        print("🧪 Starting Sous Chef Linguine Admin Panel API Tests")
        print("Testing admin authentication, recipe management, and JSON import")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 70)
        
        # Test 1: Admin Authentication - Valid Password
        self.test_admin_login_success()
        
        # Test 2: Admin Authentication - Invalid Password  
        self.test_admin_login_failure()
        
        # Test 3: Admin Token Verification
        self.test_admin_verify_token()
        
        # Test 4: Admin Recipe Management - Get All Recipes
        self.test_admin_recipes_list()
        
        # Test 5: Admin Recipe Management - Get Single Recipe
        self.test_admin_single_recipe()
        
        # Test 6: Admin JSON Import & Duplicate Detection
        self.test_admin_json_import()
        
        # Test 7: Admin Dashboard Statistics
        self.test_admin_stats()
        
        # Test 8: CSV Template
        self.test_csv_template()
        
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
            print(f"\n✅ ALL TESTS PASSED - Admin Panel APIs working correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = AdminPanelTester()
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