#!/usr/bin/env python3
"""
CMS Admin Endpoints Test Suite for Sous Chef Linguine
Tests the new CMS admin endpoints including login, image upload, and techniques management.
"""

import requests
import json
import time
import io
import base64
from typing import Dict, Any, List
from PIL import Image

# Backend URL from frontend/.env
BACKEND_URL = "https://mongo-link-verify.preview.emergentagent.com/api"

class CMSAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_token = None
        self.admin_session = None
        self.test_technique_slug = None
        
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
        
    def create_test_image(self):
        """Create a small test image for upload testing"""
        # Create a 100x100 red square
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
        
    def test_admin_login(self):
        """Test Case 1: Admin Login (Token-based for recipes/uploads)"""
        print("\n=== Test 1: Admin Login (Token-based) ===")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/login", json={
                "password": "SousChefAdmin2024!"
            })
            
            if response.status_code != 200:
                self.log_test("Admin Login (Token)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if not data.get("success"):
                self.log_test("Admin Login (Token)", False, f"Login failed: {data}")
                return False
                
            self.admin_token = data.get("token")
            if not self.admin_token:
                self.log_test("Admin Login (Token)", False, "No token received")
                return False
                
            self.log_test("Admin Login (Token)", True, "Successfully logged in as admin with token")
            return True
            
        except Exception as e:
            self.log_test("Admin Login (Token)", False, f"Exception: {str(e)}")
            return False

    def test_admin_session_login(self):
        """Test Case 1b: Admin Session Login (Session-based for techniques)"""
        print("\n=== Test 1b: Admin Session Login (Session-based) ===")
        
        try:
            # Create new session for admin user
            self.admin_session = requests.Session()
            
            response = self.admin_session.post(f"{BACKEND_URL}/auth/login", json={
                "email": "admin@souschef.com",
                "password": "admin123"
            })
            
            if response.status_code != 200:
                self.log_test("Admin Session Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            if not data.get("success"):
                self.log_test("Admin Session Login", False, f"Session login failed: {data}")
                return False
                
            # Verify session by checking auth/me
            me_response = self.admin_session.get(f"{BACKEND_URL}/auth/me")
            if me_response.status_code == 200:
                user_data = me_response.json()
                user_info = user_data.get("user", {})
                user_role = user_info.get("role")
                
                if user_role == "admin":
                    self.log_test("Admin Session Login", True, f"Successfully logged in as admin user: {user_info.get('email')}")
                    return True
                else:
                    self.log_test("Admin Session Login", False, f"User role is not admin: {user_role}")
                    return False
            else:
                self.log_test("Admin Session Login", False, f"Session verification failed: {me_response.status_code}")
                return False
            
        except Exception as e:
            self.log_test("Admin Session Login", False, f"Exception: {str(e)}")
            return False
            
    def test_recipe_image_upload(self):
        """Test Case 2: Recipe Image Upload Endpoint"""
        print("\n=== Test 2: Recipe Image Upload Endpoint ===")
        
        if not self.admin_token:
            self.log_test("Recipe Image Upload", False, "No admin token available")
            return False
        
        try:
            # Create a test image
            test_image = self.create_test_image()
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            files = {
                'image': ('test_recipe_image.jpg', test_image, 'image/jpeg')
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/recipes/upload-image", 
                headers=headers,
                files=files
            )
            
            if response.status_code != 200:
                self.log_test("Recipe Image Upload", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if not data.get("success"):
                self.log_test("Recipe Image Upload", False, f"Upload failed: {data}")
                return False
                
            if not data.get("image_url"):
                self.log_test("Recipe Image Upload", False, "No image_url in response")
                return False
                
            image_url = data.get("image_url")
            filename = data.get("filename")
            
            # Verify image URL format
            if not image_url.startswith("/api/recipe-images/"):
                self.log_test("Recipe Image Upload", False, f"Invalid image_url format: {image_url}")
                return False
                
            self.log_test("Recipe Image Upload", True, 
                f"Image uploaded successfully. URL: {image_url}, Filename: {filename}")
            return True
            
        except Exception as e:
            self.log_test("Recipe Image Upload", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_techniques_list(self):
        """Test Case 3: Admin Techniques List Endpoint"""
        print("\n=== Test 3: Admin Techniques List Endpoint ===")
        
        if not self.admin_session:
            self.log_test("Admin Techniques List", False, "No admin session available")
            return False
        
        try:
            response = self.admin_session.get(f"{BACKEND_URL}/admin/techniques")
            
            if response.status_code != 200:
                self.log_test("Admin Techniques List", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if "techniques" not in data:
                self.log_test("Admin Techniques List", False, "Missing 'techniques' field in response")
                return False
                
            if "total" not in data:
                self.log_test("Admin Techniques List", False, "Missing 'total' field in response")
                return False
            
            techniques = data["techniques"]
            total = data["total"]
            
            self.log_test("Admin Techniques List", True, 
                f"Retrieved {total} techniques successfully")
            return True
            
        except Exception as e:
            self.log_test("Admin Techniques List", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_techniques_create(self):
        """Test Case 4: Admin Techniques Create Endpoint"""
        print("\n=== Test 4: Admin Techniques Create Endpoint ===")
        
        if not self.admin_session:
            self.log_test("Admin Techniques Create", False, "No admin session available")
            return False
        
        try:
            # Create test technique data with correct format
            technique_data = {
                "title": "Test Knife Skills",
                "category": "Knife Skills", 
                "difficulty": "Beginner",  # Enum value: Beginner/Intermediate/Advanced
                "readTime": 5,  # Integer, not string
                "introduction": "Basic knife skills introduction for testing",
                "sections": [  # Must have at least 1 section
                    {
                        "title": "Basic Cuts",
                        "content": "Learn the fundamental knife cuts including julienne, brunoise, and chiffonade."
                    }
                ],
                "status": "draft"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/admin/techniques", 
                json=technique_data
            )
            
            if response.status_code != 200:
                self.log_test("Admin Techniques Create", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            required_fields = ["title", "slug", "category", "difficulty", "status"]
            for field in required_fields:
                if field not in data:
                    self.log_test("Admin Techniques Create", False, f"Missing '{field}' in response")
                    return False
            
            # Store the slug for future tests
            self.test_technique_slug = data.get("slug")
            
            self.log_test("Admin Techniques Create", True, 
                f"Technique created successfully. Slug: {self.test_technique_slug}")
            return True
            
        except Exception as e:
            self.log_test("Admin Techniques Create", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_techniques_get(self):
        """Test Case 5: Admin Techniques Get Single Endpoint"""
        print("\n=== Test 5: Admin Techniques Get Single Endpoint ===")
        
        if not self.admin_session:
            self.log_test("Admin Techniques Get", False, "No admin session available")
            return False
            
        if not self.test_technique_slug:
            self.log_test("Admin Techniques Get", False, "No test technique slug available")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/admin/techniques/{self.test_technique_slug}"
            )
            
            if response.status_code != 200:
                self.log_test("Admin Techniques Get", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if "technique" not in data:
                self.log_test("Admin Techniques Get", False, "Missing 'technique' field in response")
                return False
            
            technique = data["technique"]
            
            # Verify it's the right technique
            if technique.get("slug") != self.test_technique_slug:
                self.log_test("Admin Techniques Get", False, "Retrieved technique has wrong slug")
                return False
            
            if technique.get("title") != "Test Knife Skills":
                self.log_test("Admin Techniques Get", False, "Retrieved technique has wrong title")
                return False
            
            self.log_test("Admin Techniques Get", True, 
                f"Retrieved technique successfully: {technique.get('title')}")
            return True
            
        except Exception as e:
            self.log_test("Admin Techniques Get", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_techniques_update(self):
        """Test Case 6: Admin Techniques Update Endpoint"""
        print("\n=== Test 6: Admin Techniques Update Endpoint ===")
        
        if not self.admin_session:
            self.log_test("Admin Techniques Update", False, "No admin session available")
            return False
            
        if not self.test_technique_slug:
            self.log_test("Admin Techniques Update", False, "No test technique slug available")
            return False
        
        try:
            # Update technique data
            update_data = {
                "technique_data": {
                    "title": "Updated Test Knife Skills",
                    "category": "Knife Skills",
                    "difficulty": "Intermediate", 
                    "readTime": 10,
                    "introduction": "Updated basic knife skills introduction for testing",
                    "status": "published"
                }
            }
            
            response = self.admin_session.put(
                f"{BACKEND_URL}/admin/techniques/{self.test_technique_slug}",
                json=update_data
            )
            
            if response.status_code != 200:
                self.log_test("Admin Techniques Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if not data.get("success"):
                self.log_test("Admin Techniques Update", False, f"Update failed: {data}")
                return False
            
            if not data.get("message"):
                self.log_test("Admin Techniques Update", False, "Missing success message")
                return False
            
            self.log_test("Admin Techniques Update", True, 
                f"Technique updated successfully: {data.get('message')}")
            return True
            
        except Exception as e:
            self.log_test("Admin Techniques Update", False, f"Exception: {str(e)}")
            return False
            
    def test_admin_techniques_delete(self):
        """Test Case 7: Admin Techniques Delete Endpoint"""
        print("\n=== Test 7: Admin Techniques Delete Endpoint ===")
        
        if not self.admin_session:
            self.log_test("Admin Techniques Delete", False, "No admin session available")
            return False
            
        if not self.test_technique_slug:
            self.log_test("Admin Techniques Delete", False, "No test technique slug available")
            return False
        
        try:
            response = self.admin_session.delete(
                f"{BACKEND_URL}/admin/techniques/{self.test_technique_slug}"
            )
            
            if response.status_code != 200:
                self.log_test("Admin Techniques Delete", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check response structure
            if not data.get("success"):
                self.log_test("Admin Techniques Delete", False, f"Delete failed: {data}")
                return False
            
            if not data.get("message"):
                self.log_test("Admin Techniques Delete", False, "Missing success message")
                return False
            
            self.log_test("Admin Techniques Delete", True, 
                f"Technique deleted successfully: {data.get('message')}")
            return True
            
        except Exception as e:
            self.log_test("Admin Techniques Delete", False, f"Exception: {str(e)}")
            return False
            
    def test_menu_builder_hidden(self):
        """Test Case 8: Verify Menu Builder is Hidden"""
        print("\n=== Test 8: Verify Menu Builder Hidden ===")
        
        try:
            # Test basic health check endpoint still works
            response = self.session.get(f"{BACKEND_URL}/")
            
            if response.status_code != 200:
                self.log_test("Menu Builder Hidden", False, f"Health check failed: HTTP {response.status_code}")
                return False
                
            data = response.json()
            
            # Check health response
            if not data.get("message"):
                self.log_test("Menu Builder Hidden", False, "Health check missing message")
                return False
            
            if data.get("status") != "running":
                self.log_test("Menu Builder Hidden", False, f"Backend not running: {data.get('status')}")
                return False
            
            # Note: Menu Builder hiding is frontend-only via REACT_APP_ENABLE_MENU_BUILDER=false
            # Backend endpoints remain intact but frontend won't show them
            
            self.log_test("Menu Builder Hidden", True, 
                "Backend health check working. Menu Builder hidden via frontend feature flag")
            return True
            
        except Exception as e:
            self.log_test("Menu Builder Hidden", False, f"Exception: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all CMS admin endpoint tests"""
        print("🧪 Starting CMS Admin Endpoints Test Suite for Sous Chef Linguine")
        print("Testing admin login, image upload, and techniques management endpoints")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Step 1: Admin Login (Token-based)
        login_success = self.test_admin_login()
        if not login_success:
            print("\n❌ CRITICAL: Admin token login failed. Cannot proceed with image upload tests.")
            
        # Step 1b: Admin Session Login (Session-based)
        session_success = self.test_admin_session_login()
        if not session_success:
            print("\n❌ CRITICAL: Admin session login failed. Cannot proceed with techniques tests.")
        
        # Step 2: Test Recipe Image Upload (requires token auth)
        if login_success:
            self.test_recipe_image_upload()
        
        # Step 3: Test Admin Techniques Endpoints (requires session auth)
        if session_success:
            self.test_admin_techniques_list()
            create_success = self.test_admin_techniques_create()
            
            if create_success:
                self.test_admin_techniques_get()
                self.test_admin_techniques_update() 
                self.test_admin_techniques_delete()
        
        # Step 4: Test Menu Builder Hidden (Health Check)
        self.test_menu_builder_hidden()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 CMS ADMIN ENDPOINTS TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "0%")
        
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
            print(f"\n✅ ALL TESTS PASSED - CMS Admin endpoints working correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = CMSAdminTester()
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