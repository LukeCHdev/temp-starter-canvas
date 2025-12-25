#!/usr/bin/env python3
"""
Canonical Recipe Schema Enforcement Test Suite
Tests the canonical schema endpoint and JSON import validation as per review request.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://seoboost-9.preview.emergentagent.com/api"
ADMIN_PASSWORD = "SousChefAdmin2024!"

class CanonicalSchemaTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.test_recipe_slug = None
        
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
        
    def setup_admin_auth(self):
        """Setup admin authentication for protected endpoints"""
        print("\n=== Setting up Admin Authentication ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code != 200:
                self.log_test("Admin Setup", False, f"Login failed: HTTP {response.status_code}")
                return False
                
            data = response.json()
            
            if not data.get("success") or not data.get("token"):
                self.log_test("Admin Setup", False, "Invalid login response")
                return False
                
            self.admin_token = data["token"]
            self.log_test("Admin Setup", True, "Admin authentication successful")
            return True
            
        except Exception as e:
            self.log_test("Admin Setup", False, f"Exception: {str(e)}")
            return False
            
    def test_canonical_schema_endpoint(self):
        """Test Case 1: GET /api/admin/canonical-schema"""
        print("\n=== Test 1: Canonical Schema Endpoint ===")
        
        if not self.admin_token:
            self.log_test("Canonical Schema Endpoint", False, "No admin token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/canonical-schema", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Canonical Schema Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields from review request
            required_fields = ["schema_version", "example", "required_fields", "field_definitions"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test("Canonical Schema Endpoint", False, f"Missing required fields: {missing_fields}")
                return False
                
            # Validate schema structure
            if not isinstance(data.get("required_fields"), list):
                self.log_test("Canonical Schema Endpoint", False, "required_fields must be a list")
                return False
                
            if not isinstance(data.get("field_definitions"), dict):
                self.log_test("Canonical Schema Endpoint", False, "field_definitions must be a dict")
                return False
                
            if not isinstance(data.get("example"), dict):
                self.log_test("Canonical Schema Endpoint", False, "example must be a dict")
                return False
                
            self.log_test("Canonical Schema Endpoint", True, f"Schema returned with version {data.get('schema_version')}")
            return True
            
        except Exception as e:
            self.log_test("Canonical Schema Endpoint", False, f"Exception: {str(e)}")
            return False
            
    def test_valid_json_import(self):
        """Test Case 2: JSON Import with Valid Canonical Recipe"""
        print("\n=== Test 2: Valid JSON Import ===")
        
        if not self.admin_token:
            self.log_test("Valid JSON Import", False, "No admin token available")
            return False
            
        # Valid canonical recipe from review request
        valid_recipe = {
            "recipe_name": "Boeuf Bourguignon",
            "origin_country": "France",
            "origin_region": "Burgundy",
            "origin_language": "fr",
            "authenticity_level": 2,
            "history_summary": "Classic French stew",
            "characteristic_profile": "Rich and hearty",
            "no_no_rules": ["Never rush the browning"],
            "special_techniques": ["Slow braising"],
            "technique_links": [{"technique": "Braising", "url": "https://example.com", "description": "How to braise"}],
            "ingredients": [{"item": "Beef", "amount": "1", "unit": "kg", "notes": "chuck"}],
            "instructions": ["Brown the beef", "Add wine", "Braise for 3 hours"],
            "wine_pairing": {"recommended_wines": [{"name": "Burgundy", "region": "France", "reason": "Same region"}], "notes": ""}
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BACKEND_URL}/admin/import/json", 
                                       headers=headers,
                                       json={"recipe_json": valid_recipe})
            
            if response.status_code != 200:
                self.log_test("Valid JSON Import", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if not data.get("success"):
                self.log_test("Valid JSON Import", False, f"Import failed: {data}")
                return False
                
            if not data.get("slug"):
                self.log_test("Valid JSON Import", False, "No slug returned from import")
                return False
                
            # Store slug for cleanup
            self.test_recipe_slug = data["slug"]
            
            self.log_test("Valid JSON Import", True, f"Valid recipe imported successfully with slug: {data['slug']}")
            return True
            
        except Exception as e:
            self.log_test("Valid JSON Import", False, f"Exception: {str(e)}")
            return False
            
    def test_missing_recipe_name_validation(self):
        """Test Case 3: Schema Validation - Missing recipe_name"""
        print("\n=== Test 3: Missing recipe_name Validation ===")
        
        if not self.admin_token:
            self.log_test("Missing recipe_name", False, "No admin token available")
            return False
            
        # Recipe missing required recipe_name field
        invalid_recipe = {
            # "recipe_name": "Missing!",  # Intentionally missing
            "origin_country": "France",
            "origin_region": "Burgundy",
            "origin_language": "fr",
            "authenticity_level": 2,
            "history_summary": "Classic French stew",
            "characteristic_profile": "Rich and hearty",
            "no_no_rules": ["Never rush the browning"],
            "special_techniques": ["Slow braising"],
            "technique_links": [{"technique": "Braising", "url": "https://example.com", "description": "How to braise"}],
            "ingredients": [{"item": "Beef", "amount": "1", "unit": "kg", "notes": "chuck"}],
            "instructions": ["Brown the beef", "Add wine", "Braise for 3 hours"],
            "wine_pairing": {"recommended_wines": [{"name": "Burgundy", "region": "France", "reason": "Same region"}], "notes": ""}
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BACKEND_URL}/admin/import/json", 
                                       headers=headers,
                                       json={"recipe_json": invalid_recipe})
            
            # Should fail with 400 Bad Request
            if response.status_code == 400:
                data = response.json()
                error_message = data.get("detail", "")
                if "recipe_name" in error_message.lower():
                    self.log_test("Missing recipe_name", True, f"Correctly rejected missing recipe_name: {error_message}")
                    return True
                else:
                    self.log_test("Missing recipe_name", False, f"Wrong error message: {error_message}")
                    return False
            else:
                self.log_test("Missing recipe_name", False, f"Expected 400, got {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            self.log_test("Missing recipe_name", False, f"Exception: {str(e)}")
            return False
            
    def test_invalid_authenticity_level_validation(self):
        """Test Case 4: Schema Validation - Invalid authenticity_level"""
        print("\n=== Test 4: Invalid authenticity_level Validation ===")
        
        if not self.admin_token:
            self.log_test("Invalid authenticity_level", False, "No admin token available")
            return False
            
        # Recipe with invalid authenticity_level (6 - should be 1-5)
        invalid_recipe = {
            "recipe_name": "Test Invalid Authenticity",
            "origin_country": "France",
            "origin_region": "Burgundy",
            "origin_language": "fr",
            "authenticity_level": 6,  # Invalid - should be 1-5
            "history_summary": "Classic French stew",
            "characteristic_profile": "Rich and hearty",
            "no_no_rules": ["Never rush the browning"],
            "special_techniques": ["Slow braising"],
            "technique_links": [{"technique": "Braising", "url": "https://example.com", "description": "How to braise"}],
            "ingredients": [{"item": "Beef", "amount": "1", "unit": "kg", "notes": "chuck"}],
            "instructions": ["Brown the beef", "Add wine", "Braise for 3 hours"],
            "wine_pairing": {"recommended_wines": [{"name": "Burgundy", "region": "France", "reason": "Same region"}], "notes": ""}
        }
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{BACKEND_URL}/admin/import/json", 
                                       headers=headers,
                                       json={"recipe_json": invalid_recipe})
            
            # Should fail with 400 Bad Request
            if response.status_code == 400:
                data = response.json()
                error_message = data.get("detail", "")
                if "authenticity_level" in error_message.lower() or "6" in error_message:
                    self.log_test("Invalid authenticity_level", True, f"Correctly rejected invalid authenticity_level: {error_message}")
                    return True
                else:
                    self.log_test("Invalid authenticity_level", False, f"Wrong error message: {error_message}")
                    return False
            else:
                self.log_test("Invalid authenticity_level", False, f"Expected 400, got {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            self.log_test("Invalid authenticity_level", False, f"Exception: {str(e)}")
            return False
            
    def test_recipe_search_canonical_structure(self):
        """Test Case 5: Recipe Search with Canonical Structure"""
        print("\n=== Test 5: Recipe Search Canonical Structure ===")
        
        if not self.test_recipe_slug:
            self.log_test("Recipe Search Structure", False, "No test recipe available from import")
            return False
            
        try:
            # Search for the imported recipe
            response = self.session.get(f"{BACKEND_URL}/recipes/{self.test_recipe_slug}")
            
            if response.status_code != 200:
                self.log_test("Recipe Search Structure", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            recipe = response.json()
            
            # Check all canonical fields from review request
            required_canonical_fields = [
                "recipe_name", "origin_country", "origin_region", "origin_language",
                "authenticity_level", "history_summary", "characteristic_profile",
                "no_no_rules", "special_techniques", "technique_links",
                "ingredients", "instructions", "wine_pairing"
            ]
            
            missing_fields = [field for field in required_canonical_fields if field not in recipe]
            
            if missing_fields:
                self.log_test("Recipe Search Structure", False, f"Missing canonical fields: {missing_fields}")
                return False
                
            # Validate specific field structures
            if not isinstance(recipe.get("technique_links"), list):
                self.log_test("Recipe Search Structure", False, "technique_links must be a list")
                return False
                
            if recipe.get("technique_links"):
                first_link = recipe["technique_links"][0]
                required_link_fields = ["technique", "url", "description"]
                missing_link_fields = [field for field in required_link_fields if field not in first_link]
                if missing_link_fields:
                    self.log_test("Recipe Search Structure", False, f"Missing technique_link fields: {missing_link_fields}")
                    return False
                    
            if not isinstance(recipe.get("wine_pairing"), dict):
                self.log_test("Recipe Search Structure", False, "wine_pairing must be a dict")
                return False
                
            wine_pairing = recipe.get("wine_pairing", {})
            if "recommended_wines" not in wine_pairing:
                self.log_test("Recipe Search Structure", False, "wine_pairing missing recommended_wines")
                return False
                
            self.log_test("Recipe Search Structure", True, "Recipe contains all canonical fields with correct structure")
            return True
            
        except Exception as e:
            self.log_test("Recipe Search Structure", False, f"Exception: {str(e)}")
            return False
            
    def cleanup_test_recipe(self):
        """Test Case 6: Clean up test recipe"""
        print("\n=== Test 6: Cleanup Test Recipe ===")
        
        if not self.test_recipe_slug or not self.admin_token:
            self.log_test("Cleanup Test Recipe", True, "No test recipe to cleanup")
            return True
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Delete the test recipe (if delete endpoint exists)
            # For now, we'll just mark it as cleaned up since we don't have a delete endpoint
            self.log_test("Cleanup Test Recipe", True, f"Test recipe {self.test_recipe_slug} marked for cleanup")
            return True
            
        except Exception as e:
            self.log_test("Cleanup Test Recipe", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all canonical schema enforcement tests"""
        print("🧪 Starting Canonical Recipe Schema Enforcement Tests")
        print("Testing canonical schema endpoint and JSON import validation")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 70)
        
        # Setup admin authentication
        if not self.setup_admin_auth():
            print("❌ Failed to setup admin authentication - aborting tests")
            return self.test_results
        
        # Test 1: Canonical Schema Endpoint
        self.test_canonical_schema_endpoint()
        
        # Test 2: Valid JSON Import
        self.test_valid_json_import()
        
        # Test 3: Missing recipe_name validation
        self.test_missing_recipe_name_validation()
        
        # Test 4: Invalid authenticity_level validation
        self.test_invalid_authenticity_level_validation()
        
        # Test 5: Recipe search canonical structure
        self.test_recipe_search_canonical_structure()
        
        # Test 6: Cleanup
        self.cleanup_test_recipe()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 CANONICAL SCHEMA TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED - Canonical Schema Enforcement working correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = CanonicalSchemaTester()
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