"""
Tests for Admin Batch Image Generation Endpoints
=================================================
Features to test:
1. POST /api/admin/images/generate-batch?dry_run=true - returns count and list of missing recipes
2. POST /api/admin/images/generate-batch - starts background job, returns immediately
3. GET /api/admin/images/status - returns progress (running, generated, failed, skipped, cost)
4. Duplicate batch start blocked with appropriate message
5. Both endpoints require admin auth (reject no token, wrong token)
6. Already-generated images are not regenerated
7. Static serving: GET /api/recipe-images/{slug}.webp returns 200 image/webp
"""

import pytest
import requests
import os
import base64
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_PASSWORD = "SousChefAdmin2024!"


# ============== FIXTURES ==============

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.fail("Admin login failed - cannot proceed with tests")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


# ============== AUTH TESTS ==============

class TestAdminAuthRequired:
    """Test that both batch endpoints require admin authentication"""
    
    def test_generate_batch_no_token(self, api_client):
        """POST /api/admin/images/generate-batch without token returns 401"""
        response = api_client.post(f"{BASE_URL}/api/admin/images/generate-batch")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ generate-batch returns 401 without token")

    def test_generate_batch_invalid_token(self, api_client):
        """POST /api/admin/images/generate-batch with wrong token returns 401"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/images/generate-batch",
            headers={"Authorization": "Bearer invalid_token_123"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ generate-batch returns 401 with invalid token")

    def test_status_no_token(self, api_client):
        """GET /api/admin/images/status without token returns 401"""
        response = api_client.get(f"{BASE_URL}/api/admin/images/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ status returns 401 without token")

    def test_status_invalid_token(self, api_client):
        """GET /api/admin/images/status with wrong token returns 401"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/images/status",
            headers={"Authorization": "Bearer wrong_token"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ status returns 401 with invalid token")


# ============== DRY RUN TESTS ==============

class TestDryRunEndpoint:
    """Test POST /api/admin/images/generate-batch?dry_run=true"""
    
    def test_dry_run_returns_count_and_list(self, api_client, auth_headers):
        """Dry run returns recipes missing images and estimated cost"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/images/generate-batch?dry_run=true",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "dry_run" in data, "Response must have 'dry_run' field"
        assert data["dry_run"] is True, "dry_run should be True"
        
        assert "recipes_missing_images" in data, "Response must have 'recipes_missing_images'"
        assert isinstance(data["recipes_missing_images"], int), "recipes_missing_images should be int"
        
        assert "estimated_cost_usd" in data, "Response must have 'estimated_cost_usd'"
        assert isinstance(data["estimated_cost_usd"], (int, float)), "estimated_cost_usd should be numeric"
        
        assert "recipes" in data, "Response must have 'recipes' list"
        assert isinstance(data["recipes"], list), "recipes should be a list"
        
        assert "batch_size" in data, "Response must have 'batch_size'"
        
        print(f"✓ Dry run returned: {data['recipes_missing_images']} missing images, ${data['estimated_cost_usd']} estimated")
        print(f"  Sample recipes: {[r['slug'] for r in data['recipes'][:5]]}")

    def test_dry_run_recipe_structure(self, api_client, auth_headers):
        """Dry run recipes list has correct structure (slug, name)"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/images/generate-batch?dry_run=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        recipes = data.get("recipes", [])
        
        # If there are recipes missing images, verify structure
        if recipes:
            recipe = recipes[0]
            assert "slug" in recipe, "Recipe should have 'slug'"
            assert "name" in recipe, "Recipe should have 'name'"
            print(f"✓ Recipe structure correct: {recipe}")
        else:
            print("✓ No recipes missing images (all have images)")

    def test_dry_run_cost_calculation(self, api_client, auth_headers):
        """Dry run cost estimate is calculated correctly ($0.04 per image)"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/images/generate-batch?dry_run=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        missing_count = data.get("recipes_missing_images", 0)
        estimated_cost = data.get("estimated_cost_usd", 0)
        
        expected_cost = round(missing_count * 0.04, 2)
        assert estimated_cost == expected_cost, f"Expected ${expected_cost}, got ${estimated_cost}"
        print(f"✓ Cost calculation correct: {missing_count} images × $0.04 = ${estimated_cost}")


# ============== STATUS ENDPOINT TESTS ==============

class TestStatusEndpoint:
    """Test GET /api/admin/images/status"""
    
    def test_status_returns_progress_fields(self, api_client, auth_headers):
        """Status endpoint returns all required progress fields"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/images/status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Required fields
        required_fields = [
            "running", "total", "progress_pct", "generated", 
            "failed", "skipped", "cost_estimate_usd", "current_slug",
            "started_at", "finished_at", "recent_log"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Type checks
        assert isinstance(data["running"], bool), "running should be bool"
        assert isinstance(data["total"], int), "total should be int"
        assert isinstance(data["progress_pct"], (int, float)), "progress_pct should be numeric"
        assert isinstance(data["generated"], int), "generated should be int"
        assert isinstance(data["failed"], int), "failed should be int"
        assert isinstance(data["skipped"], int), "skipped should be int"
        assert isinstance(data["cost_estimate_usd"], (int, float)), "cost_estimate_usd should be numeric"
        assert isinstance(data["recent_log"], list), "recent_log should be list"
        
        print(f"✓ Status endpoint returned all fields")
        print(f"  running={data['running']}, generated={data['generated']}, failed={data['failed']}, skipped={data['skipped']}")

    def test_status_progress_calculation(self, api_client, auth_headers):
        """Progress percentage is calculated correctly"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/images/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        total = data.get("total", 0)
        done = data["generated"] + data["failed"] + data["skipped"]
        progress = data["progress_pct"]
        
        if total > 0:
            expected_progress = round(done / total * 100, 1)
            assert progress == expected_progress, f"Expected {expected_progress}%, got {progress}%"
            print(f"✓ Progress calculation correct: {done}/{total} = {progress}%")
        else:
            assert progress == 0, "Progress should be 0 when total is 0"
            print("✓ Progress is 0 (no job run yet or no recipes to process)")


# ============== DUPLICATE JOB PREVENTION TESTS ==============

class TestDuplicateJobPrevention:
    """Test that duplicate batch jobs are blocked"""
    
    def test_check_if_job_already_running(self, api_client, auth_headers):
        """Check status to see if a job is currently running"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/images/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        is_running = data.get("running", False)
        
        print(f"✓ Current job status: running={is_running}")
        
        if is_running:
            print(f"  A batch job is currently running")
            print(f"  Current slug: {data.get('current_slug')}")
            print(f"  Progress: {data.get('progress_pct')}%")
            
            # Attempt to start another job - should be blocked
            start_response = api_client.post(
                f"{BASE_URL}/api/admin/images/generate-batch",
                headers=auth_headers
            )
            assert start_response.status_code == 200
            start_data = start_response.json()
            
            # Verify it was blocked
            assert start_data.get("started") is False, "Job should not have started"
            assert "already running" in start_data.get("message", "").lower(), \
                f"Message should indicate job already running: {start_data.get('message')}"
            print("✓ Duplicate job correctly blocked")
        else:
            print("  No job currently running")


# ============== STATIC IMAGE SERVING TESTS ==============

class TestStaticImageServing:
    """Test that generated images are served correctly"""
    
    def test_serve_pizza_margherita_webp(self, api_client):
        """GET /api/recipe-images/pizza-margherita-italy.webp returns 200 image/webp"""
        response = api_client.get(
            f"{BASE_URL}/api/recipe-images/pizza-margherita-italy.webp"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get("content-type", "")
        assert "image/webp" in content_type, f"Expected image/webp, got {content_type}"
        
        # Verify it's a real image (check file size)
        content_length = len(response.content)
        assert content_length > 10000, f"Image too small: {content_length} bytes"
        
        print(f"✓ pizza-margherita-italy.webp served: {content_length // 1024}KB, {content_type}")

    def test_serve_risotto_webp(self, api_client):
        """GET /api/recipe-images/risotto-alla-milanese-italy.webp returns 200"""
        response = api_client.get(
            f"{BASE_URL}/api/recipe-images/risotto-alla-milanese-italy.webp"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get("content-type", "")
        assert "image/webp" in content_type
        print(f"✓ risotto-alla-milanese-italy.webp served: {len(response.content) // 1024}KB")

    def test_serve_coq_au_vin_webp(self, api_client):
        """GET /api/recipe-images/coq-au-vin-france.webp returns 200"""
        response = api_client.get(
            f"{BASE_URL}/api/recipe-images/coq-au-vin-france.webp"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        content_type = response.headers.get("content-type", "")
        assert "image/webp" in content_type
        print(f"✓ coq-au-vin-france.webp served: {len(response.content) // 1024}KB")

    def test_nonexistent_image_returns_404(self, api_client):
        """GET /api/recipe-images/nonexistent-recipe.webp returns 404"""
        response = api_client.get(
            f"{BASE_URL}/api/recipe-images/does-not-exist-xyz.webp"
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent image, got {response.status_code}"
        print("✓ Nonexistent image returns 404")


# ============== RECIPE API IMAGE URL VERIFICATION ==============

class TestRecipeImageURLInAPI:
    """Verify that recipes with generated images have image_url in API response"""
    
    def test_pizza_margherita_has_image_url(self, api_client):
        """Pizza Margherita recipe should have image_url in API response"""
        response = api_client.get(f"{BASE_URL}/api/recipes/pizza-margherita-italy")
        
        # Recipe might not exist, skip if 404
        if response.status_code == 404:
            pytest.skip("Recipe pizza-margherita-italy not found")
        
        assert response.status_code == 200
        data = response.json()
        recipe = data.get("recipe", data)  # Handle different response formats
        
        image_url = recipe.get("image_url")
        assert image_url is not None, "Recipe should have image_url"
        assert "pizza-margherita-italy" in image_url, f"image_url should contain slug: {image_url}"
        
        print(f"✓ pizza-margherita-italy has image_url: {image_url}")

    def test_risotto_has_image_url(self, api_client):
        """Risotto recipe should have image_url in API response"""
        response = api_client.get(f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy")
        
        if response.status_code == 404:
            pytest.skip("Recipe risotto-alla-milanese-italy not found")
        
        assert response.status_code == 200
        data = response.json()
        recipe = data.get("recipe", data)
        
        image_url = recipe.get("image_url")
        assert image_url is not None, "Recipe should have image_url"
        print(f"✓ risotto-alla-milanese-italy has image_url: {image_url}")

    def test_coq_au_vin_has_image_url(self, api_client):
        """Coq au Vin recipe should have image_url in API response"""
        response = api_client.get(f"{BASE_URL}/api/recipes/coq-au-vin-france")
        
        if response.status_code == 404:
            pytest.skip("Recipe coq-au-vin-france not found")
        
        assert response.status_code == 200
        data = response.json()
        recipe = data.get("recipe", data)
        
        image_url = recipe.get("image_url")
        assert image_url is not None, "Recipe should have image_url"
        print(f"✓ coq-au-vin-france has image_url: {image_url}")


# ============== ADMIN LOGIN TEST ==============

class TestAdminLogin:
    """Test admin authentication flow"""
    
    def test_admin_login_success(self, api_client):
        """Admin login with correct password returns token"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/login",
            json={"password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") is True, "Login should succeed"
        assert "token" in data, "Response should contain token"
        assert len(data["token"]) > 0, "Token should not be empty"
        
        print(f"✓ Admin login successful, token received")

    def test_admin_login_wrong_password(self, api_client):
        """Admin login with wrong password returns 401"""
        response = api_client.post(
            f"{BASE_URL}/api/admin/login",
            json={"password": "wrong_password_123"}
        )
        assert response.status_code == 401, f"Expected 401 for wrong password, got {response.status_code}"
        print("✓ Admin login rejected for wrong password")


# ============== RUN TESTS ==============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
