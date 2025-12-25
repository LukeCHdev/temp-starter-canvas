#!/usr/bin/env python3
"""
Backend Test Suite for Sous Chef Linguine Prerendering System
Tests prerendering APIs for SEO-optimized content delivery to crawlers.
"""

import requests
import json
import time
import re
from typing import Dict, Any, List

# Backend URL from frontend/.env
BACKEND_URL = "https://seoboost-9.preview.emergentagent.com/api"

class PrerenderTester:
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
        
    def test_prerender_status(self):
        """Test Case 1: Prerender Status Check"""
        print("\n=== Test 1: Prerender Status Check ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/status")
            
            if response.status_code != 200:
                self.log_test("Prerender Status", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check if prerendering is enabled
            if not data.get("enabled"):
                self.log_test("Prerender Status", False, f"Expected enabled=true, got {data.get('enabled')}")
                return False
                
            # Check if crawler list exists
            if "crawlers" not in data or not isinstance(data["crawlers"], list):
                self.log_test("Prerender Status", False, "Missing or invalid 'crawlers' list")
                return False
                
            crawler_count = len(data["crawlers"])
            self.log_test("Prerender Status", True, f"Prerender enabled with {crawler_count} crawlers configured")
            return True
            
        except Exception as e:
            self.log_test("Prerender Status", False, f"Exception: {str(e)}")
            return False
            
    def test_crawler_detection(self):
        """Test Case 2: Crawler Detection"""
        print("\n=== Test 2: Crawler Detection ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/test/fr/explore?simulate_bot=true")
            
            if response.status_code != 200:
                self.log_test("Crawler Detection", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            data = response.json()
            
            # Check if crawler is detected
            if not data.get("is_crawler"):
                self.log_test("Crawler Detection", False, f"Expected is_crawler=true, got {data.get('is_crawler')}")
                return False
                
            # Check if should prerender
            if not data.get("should_prerender"):
                self.log_test("Crawler Detection", False, f"Expected should_prerender=true, got {data.get('should_prerender')}")
                return False
                
            # Check prerender status (should be either "success" or "fallback")
            prerender_status = data.get("prerender_status")
            if prerender_status not in ["success", "fallback"]:
                self.log_test("Crawler Detection", False, f"Invalid prerender_status: {prerender_status}")
                return False
                
            self.log_test("Crawler Detection", True, f"Crawler detected, prerender_status: {prerender_status}")
            return True
            
        except Exception as e:
            self.log_test("Crawler Detection", False, f"Exception: {str(e)}")
            return False
            
    def test_french_recipe_prerender(self):
        """Test Case 3: French Recipe Prerender with Full Content"""
        print("\n=== Test 3: French Recipe Prerender ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/recipe/fr/spaghetti-alla-carbonara-italy")
            
            if response.status_code != 200:
                self.log_test("French Recipe Prerender", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            html_content = response.text
            
            # Check for H1 tag with recipe name
            if not re.search(r'<h1[^>]*>.*spaghetti.*carbonara.*</h1>', html_content, re.IGNORECASE):
                self.log_test("French Recipe Prerender", False, "Missing H1 tag with recipe name")
                return False
                
            # Check for French content sections
            french_sections = ["Histoire et Origine", "Ingrédients", "Instructions"]
            missing_sections = []
            for section in french_sections:
                if section not in html_content:
                    missing_sections.append(section)
                    
            if missing_sections:
                self.log_test("French Recipe Prerender", False, f"Missing French sections: {missing_sections}")
                return False
                
            # Check for JSON-LD with Recipe type
            if '"@type": "Recipe"' not in html_content and '"@type":"Recipe"' not in html_content:
                self.log_test("French Recipe Prerender", False, "Missing JSON-LD Recipe schema")
                return False
                
            # Check for hreflang tags (should have all 5 languages)
            hreflang_count = len(re.findall(r'hreflang="[^"]*"', html_content))
            if hreflang_count < 5:
                self.log_test("French Recipe Prerender", False, f"Expected 5+ hreflang tags, found {hreflang_count}")
                return False
                
            # Check for canonical URL
            if 'rel="canonical"' not in html_content:
                self.log_test("French Recipe Prerender", False, "Missing canonical URL")
                return False
                
            # Check for no fallback indicators
            fallback_indicators = ["(EN)", "Translation pending", "Affiché en anglais"]
            found_indicators = [indicator for indicator in fallback_indicators if indicator in html_content]
            if found_indicators:
                self.log_test("French Recipe Prerender", False, f"Found fallback indicators: {found_indicators}")
                return False
                
            self.log_test("French Recipe Prerender", True, "French recipe prerender contains all required elements")
            return True
            
        except Exception as e:
            self.log_test("French Recipe Prerender", False, f"Exception: {str(e)}")
            return False
            
    def test_italian_recipe_prerender(self):
        """Test Case 4: Italian Recipe Prerender"""
        print("\n=== Test 4: Italian Recipe Prerender ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/recipe/it/spaghetti-alla-carbonara-italy")
            
            if response.status_code != 200:
                self.log_test("Italian Recipe Prerender", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            html_content = response.text
            
            # Check for Italian content sections
            italian_sections = ["Storia e Origine", "Ingredienti", "Istruzioni"]
            missing_sections = []
            for section in italian_sections:
                if section not in html_content:
                    missing_sections.append(section)
                    
            if missing_sections:
                self.log_test("Italian Recipe Prerender", False, f"Missing Italian sections: {missing_sections}")
                return False
                
            # Check for JSON-LD Recipe schema
            if '"@type": "Recipe"' not in html_content and '"@type":"Recipe"' not in html_content:
                self.log_test("Italian Recipe Prerender", False, "Missing JSON-LD Recipe schema")
                return False
                
            # Check for no fallback indicators
            fallback_indicators = ["(EN)", "Translation pending", "Mostrato in inglese"]
            found_indicators = [indicator for indicator in fallback_indicators if indicator in html_content]
            if found_indicators:
                self.log_test("Italian Recipe Prerender", False, f"Found fallback indicators: {found_indicators}")
                return False
                
            self.log_test("Italian Recipe Prerender", True, "Italian recipe prerender contains required content")
            return True
            
        except Exception as e:
            self.log_test("Italian Recipe Prerender", False, f"Exception: {str(e)}")
            return False
            
    def test_german_recipe_prerender(self):
        """Test Case 5: German Recipe Prerender"""
        print("\n=== Test 5: German Recipe Prerender ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/recipe/de/spaghetti-alla-carbonara-italy")
            
            if response.status_code != 200:
                self.log_test("German Recipe Prerender", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            html_content = response.text
            
            # Check for German content sections
            german_sections = ["Geschichte und Herkunft", "Zutaten", "Anweisungen"]
            missing_sections = []
            for section in german_sections:
                if section not in html_content:
                    missing_sections.append(section)
                    
            if missing_sections:
                self.log_test("German Recipe Prerender", False, f"Missing German sections: {missing_sections}")
                return False
                
            # Check for no fallback indicators
            fallback_indicators = ["(EN)", "Translation pending", "Auf Englisch angezeigt"]
            found_indicators = [indicator for indicator in fallback_indicators if indicator in html_content]
            if found_indicators:
                self.log_test("German Recipe Prerender", False, f"Found fallback indicators: {found_indicators}")
                return False
                
            self.log_test("German Recipe Prerender", True, "German recipe prerender contains required content")
            return True
            
        except Exception as e:
            self.log_test("German Recipe Prerender", False, f"Exception: {str(e)}")
            return False
            
    def test_explore_page_fallback(self):
        """Test Case 6: Explore Page Fallback"""
        print("\n=== Test 6: Explore Page Fallback ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/prerender/fallback/fr/explore")
            
            if response.status_code != 200:
                self.log_test("Explore Page Fallback", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            html_content = response.text
            
            # Check for French H1
            if "Explorer les Recettes" not in html_content:
                self.log_test("Explore Page Fallback", False, "Missing French H1: 'Explorer les Recettes'")
                return False
                
            # Check for JSON-LD CollectionPage
            if '"@type": "CollectionPage"' not in html_content and '"@type":"CollectionPage"' not in html_content:
                self.log_test("Explore Page Fallback", False, "Missing JSON-LD CollectionPage schema")
                return False
                
            # Check for internal links (should have some navigation links)
            link_count = len(re.findall(r'<a[^>]*href="[^"]*"[^>]*>', html_content))
            if link_count < 3:
                self.log_test("Explore Page Fallback", False, f"Expected multiple internal links, found {link_count}")
                return False
                
            self.log_test("Explore Page Fallback", True, f"Explore page fallback contains required elements with {link_count} links")
            return True
            
        except Exception as e:
            self.log_test("Explore Page Fallback", False, f"Exception: {str(e)}")
            return False
            
    def test_no_fallback_indicators(self):
        """Test Case 7: No Fallback Indicators in Prerendered Content"""
        print("\n=== Test 7: No Fallback Indicators Verification ===")
        
        # Test multiple prerendered pages to ensure no fallback indicators
        test_urls = [
            f"{BACKEND_URL}/prerender/recipe/fr/spaghetti-alla-carbonara-italy",
            f"{BACKEND_URL}/prerender/recipe/it/spaghetti-alla-carbonara-italy", 
            f"{BACKEND_URL}/prerender/recipe/de/spaghetti-alla-carbonara-italy",
            f"{BACKEND_URL}/prerender/fallback/fr/explore"
        ]
        
        prohibited_indicators = ["(EN)", "Translation pending"]
        
        for url in test_urls:
            try:
                response = self.session.get(url)
                if response.status_code != 200:
                    continue
                    
                html_content = response.text
                found_indicators = [indicator for indicator in prohibited_indicators if indicator in html_content]
                
                if found_indicators:
                    self.log_test("No Fallback Indicators", False, f"Found prohibited indicators in {url}: {found_indicators}")
                    return False
                    
            except Exception as e:
                self.log_test("No Fallback Indicators", False, f"Exception testing {url}: {str(e)}")
                return False
                
        self.log_test("No Fallback Indicators", True, "No prohibited fallback indicators found in any prerendered content")
        return True
        
    def run_all_tests(self):
        """Run all prerendering test cases based on review request"""
        print("🧪 Starting Sous Chef Linguine Prerendering System Tests")
        print("Testing prerendering APIs for SEO-optimized content delivery to crawlers")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 70)
        
        # Test 1: Prerender Status Check
        self.test_prerender_status()
        
        # Test 2: Crawler Detection
        self.test_crawler_detection()
        
        # Test 3: French Recipe Prerender with Full Content
        self.test_french_recipe_prerender()
        
        # Test 4: Italian Recipe Prerender
        self.test_italian_recipe_prerender()
        
        # Test 5: German Recipe Prerender
        self.test_german_recipe_prerender()
        
        # Test 6: Explore Page Fallback
        self.test_explore_page_fallback()
        
        # Test 7: No Fallback Indicators Verification
        self.test_no_fallback_indicators()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 PRERENDERING TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED - Prerendering system working correctly!")
            
        return self.test_results

def main():
    """Main test runner"""
    tester = PrerenderTester()
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