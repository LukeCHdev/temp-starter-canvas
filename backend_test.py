#!/usr/bin/env python3
"""
Backend Test Suite for Sous Chef Linguine Master Data Migration Verification
Tests data migration fixes for recipe visibility issues.
"""

import requests
import json
import time
import re
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://datamigration.preview.emergentagent.com/api"

class MasterDataMigrationTester:
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
        
    def admin_login(self):
        """Login as admin and get token"""
        print("\n=== Admin Login ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": "SousChefAdmin2024!"
            })
            
            if response.status_code != 200:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if not data.get("success"):
                self.log_test("Admin Login", False, f"Login failed: {data}")
                return False
                
            self.admin_token = data.get("token")
            if not self.admin_token:
                self.log_test("Admin Login", False, "No token received")
                return False
                
            self.log_test("Admin Login", True, "Successfully logged in as admin")
            return True
            
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
            
    def test_audit_visibility_endpoint(self):
        """Test Case 1: Admin Audit Visibility Endpoint"""
        print("\n=== Test 1: Admin Audit Visibility Endpoint ===")
        
        if not self.admin_token:
            self.log_test("Audit Visibility", False, "No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/audit/visibility", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Audit Visibility", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields in response
            if "summary" not in data:
                self.log_test("Audit Visibility", False, "Missing 'summary' field in response")
                return False
                
            summary = data["summary"]
            required_fields = ["total_docs", "published_total", "visible_total", "hidden_published_total"]
            
            for field in required_fields:
                if field not in summary:
                    self.log_test("Audit Visibility", False, f"Missing '{field}' in summary")
                    return False
            
            # Check the critical migration success criteria
            published_total = summary.get("published_total", 0)
            visible_total = summary.get("visible_total", 0)
            hidden_published_total = summary.get("hidden_published_total", 0)
            
            # EXPECTED: hidden_published_total should be 0, published_total should equal visible_total
            if hidden_published_total != 0:
                self.log_test("Audit Visibility", False, 
                    f"CRITICAL: hidden_published_total = {hidden_published_total}, expected 0. Migration incomplete!")
                return False
                
            if published_total != visible_total:
                self.log_test("Audit Visibility", False, 
                    f"CRITICAL: published_total ({published_total}) != visible_total ({visible_total}). Gap = {published_total - visible_total}")
                return False
                
            self.log_test("Audit Visibility", True, 
                f"Migration SUCCESS: published_total = visible_total = {visible_total}, hidden = 0")
            return True
            
        except Exception as e:
            self.log_test("Audit Visibility", False, f"Exception: {str(e)}")
            return False
            
    def test_countries_deduplication(self):
        """Test Case 2: Countries Deduplication"""
        print("\n=== Test 2: Countries Deduplication Test ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/countries")
            
            if response.status_code != 200:
                self.log_test("Countries Deduplication", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if "countries" not in data:
                self.log_test("Countries Deduplication", False, "Missing 'countries' field in response")
                return False
                
            countries = data["countries"]
            
            # Check for duplicates by canonical name
            canonical_names = []
            duplicates = []
            
            for country in countries:
                canonical = country.get("canonical", "")
                if canonical in canonical_names:
                    duplicates.append(canonical)
                else:
                    canonical_names.append(canonical)
            
            if duplicates:
                self.log_test("Countries Deduplication", False, 
                    f"Found duplicate countries: {duplicates}")
                return False
            
            # Specific check for Italy/Italia issue
            italy_variants = [c for c in countries if "ital" in c.get("canonical", "").lower()]
            if len(italy_variants) > 1:
                variant_names = [c.get("canonical") for c in italy_variants]
                self.log_test("Countries Deduplication", False, 
                    f"Found multiple Italy variants: {variant_names}")
                return False
                
            self.log_test("Countries Deduplication", True, 
                f"No duplicates found. Total unique countries: {len(countries)}")
            return True
            
        except Exception as e:
            self.log_test("Countries Deduplication", False, f"Exception: {str(e)}")
            return False
            
    def test_continent_endpoints(self):
        """Test Case 3: Continent Endpoints"""
        print("\n=== Test 3: Continent Endpoints Test ===")
        
        continents = ["europe", "asia", "americas", "africa", "oceania"]
        all_passed = True
        
        for continent in continents:
            try:
                response = self.session.get(f"{BACKEND_URL}/recipes/{continent}?page=1&limit=5")
                
                if response.status_code != 200:
                    self.log_test(f"Continent {continent.title()}", False, 
                        f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue
                    
                data = response.json()
                
                # Check response structure
                if "recipes" not in data:
                    self.log_test(f"Continent {continent.title()}", False, 
                        "Missing 'recipes' field in response")
                    all_passed = False
                    continue
                
                recipes = data["recipes"]
                
                # Check that recipes have valid data
                if recipes:
                    sample_recipe = recipes[0]
                    required_fields = ["recipe_name", "slug", "origin_country"]
                    
                    missing_fields = [field for field in required_fields 
                                    if not sample_recipe.get(field)]
                    
                    if missing_fields:
                        self.log_test(f"Continent {continent.title()}", False, 
                            f"Sample recipe missing fields: {missing_fields}")
                        all_passed = False
                        continue
                
                self.log_test(f"Continent {continent.title()}", True, 
                    f"Returned {len(recipes)} recipes with valid data")
                
            except Exception as e:
                self.log_test(f"Continent {continent.title()}", False, f"Exception: {str(e)}")
                all_passed = False
        
        return all_passed
        
    def test_admin_stats_endpoint(self):
        """Test Case 4: Admin Stats Endpoint"""
        print("\n=== Test 4: Admin Stats Endpoint Test ===")
        
        if not self.admin_token:
            self.log_test("Admin Stats", False, "No admin token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/recipes", headers=headers)
            
            if response.status_code != 200:
                self.log_test("Admin Stats", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check required fields
            if "counts" not in data:
                self.log_test("Admin Stats", False, "Missing 'counts' field in response")
                return False
                
            counts = data["counts"]
            
            if "published" not in counts:
                self.log_test("Admin Stats", False, "Missing 'published' count in response")
                return False
            
            published_count = counts["published"]
            
            # Cross-check with audit endpoint if we have that data
            if hasattr(self, '_audit_data'):
                expected_published = self._audit_data.get("summary", {}).get("published_total", 0)
                if published_count != expected_published:
                    self.log_test("Admin Stats", False, 
                        f"Published count mismatch: admin/recipes={published_count}, audit={expected_published}")
                    return False
            
            self.log_test("Admin Stats", True, 
                f"Admin stats endpoint working. Published count: {published_count}")
            return True
            
        except Exception as e:
            self.log_test("Admin Stats", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all master data migration verification tests"""
        print("🧪 Starting Sous Chef Linguine Master Data Migration Verification Tests")
        print("Testing data migration fixes for recipe visibility issues")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Step 1: Admin Login
        if not self.admin_login():
            print("\n❌ CRITICAL: Admin login failed. Cannot proceed with admin tests.")
            return self.test_results
        
        # Step 2: Test Audit Visibility Endpoint (most critical)
        audit_success = self.test_audit_visibility_endpoint()
        
        # Step 3: Test Countries Deduplication
        countries_success = self.test_countries_deduplication()
        
        # Step 4: Test Continent Endpoints
        continents_success = self.test_continent_endpoints()
        
        # Step 5: Test Admin Stats Endpoint
        stats_success = self.test_admin_stats_endpoint()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 MASTER DATA MIGRATION TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED - Master data migration successful!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = MasterDataMigrationTester()
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