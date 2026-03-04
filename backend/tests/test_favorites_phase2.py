"""
Phase 2 Favorites API Tests
Tests the favorites CRUD endpoints for authenticated and guest users
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from Phase 1
TEST_EMAIL = "phase1final@test.com"
TEST_PASSWORD = "TestPass123"

# Test recipe slug - this should exist in the database
TEST_RECIPE_SLUG = "spaghetti-alla-carbonara-italy"


class TestFavoritesAuth:
    """Test favorites endpoints require authentication"""

    @pytest.fixture(scope='class')
    def session(self):
        """Create a session with cookies"""
        return requests.Session()

    @pytest.fixture(scope='class')
    def auth_cookies(self, session):
        """Login and get auth cookies"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return session.cookies

    def test_add_favorite_requires_auth(self):
        """POST /recipes/{slug}/favorite should return 401 for guests"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        assert response.status_code == 401, f"Expected 401 for guest, got {response.status_code}"

    def test_remove_favorite_requires_auth(self):
        """DELETE /recipes/{slug}/favorite should return 401 for guests"""
        session = requests.Session()
        response = session.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        assert response.status_code == 401, f"Expected 401 for guest, got {response.status_code}"

    def test_my_favorites_requires_auth(self):
        """GET /users/me/favorites should return 401 for guests"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/users/me/favorites")
        assert response.status_code == 401, f"Expected 401 for guest, got {response.status_code}"

    def test_favorite_status_returns_false_for_guest(self):
        """GET /recipes/{slug}/favorite-status should return {favorited: false} for guests (NOT 401)"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite-status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("favorited") == False, "Guest should see favorited: false"


class TestFavoritesCRUD:
    """Test favorites CRUD operations for authenticated users"""

    @pytest.fixture(scope='class')
    def session(self):
        """Create a session with cookies"""
        return requests.Session()

    @pytest.fixture(scope='class')
    def logged_in_session(self, session):
        """Login and return session"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return session

    def test_add_favorite(self, logged_in_session):
        """POST /recipes/{slug}/favorite should add recipe to favorites"""
        # First, ensure it's not favorited (clean state)
        logged_in_session.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        
        # Add to favorites
        response = logged_in_session.post(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("favorited") == True

    def test_favorite_status_true_after_adding(self, logged_in_session):
        """GET /recipes/{slug}/favorite-status should return favorited: true after adding"""
        response = logged_in_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite-status")
        assert response.status_code == 200
        data = response.json()
        assert data.get("favorited") == True, "Should be favorited after adding"

    def test_duplicate_favorite_is_idempotent(self, logged_in_session):
        """Adding the same favorite twice should succeed (no error, return success)"""
        # Add again (should be idempotent)
        response = logged_in_session.post(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        assert response.status_code == 200, f"Expected 200 (idempotent), got {response.status_code}"
        data = response.json()
        assert data.get("success") == True
        assert data.get("favorited") == True

    def test_my_favorites_contains_recipe(self, logged_in_session):
        """GET /users/me/favorites should contain the favorited recipe"""
        response = logged_in_session.get(f"{BASE_URL}/api/users/me/favorites")
        assert response.status_code == 200
        data = response.json()
        recipes = data.get("recipes", [])
        slugs = [r.get("slug") for r in recipes]
        assert TEST_RECIPE_SLUG in slugs, f"Expected {TEST_RECIPE_SLUG} in favorites, got {slugs}"

    def test_remove_favorite(self, logged_in_session):
        """DELETE /recipes/{slug}/favorite should remove from favorites"""
        response = logged_in_session.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("favorited") == False

    def test_favorite_status_false_after_removing(self, logged_in_session):
        """GET /recipes/{slug}/favorite-status should return favorited: false after removing"""
        response = logged_in_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite-status")
        assert response.status_code == 200
        data = response.json()
        assert data.get("favorited") == False, "Should not be favorited after removing"

    def test_my_favorites_empty_after_removing(self, logged_in_session):
        """GET /users/me/favorites should be empty after removing the favorite"""
        response = logged_in_session.get(f"{BASE_URL}/api/users/me/favorites")
        assert response.status_code == 200
        data = response.json()
        recipes = data.get("recipes", [])
        slugs = [r.get("slug") for r in recipes]
        assert TEST_RECIPE_SLUG not in slugs, f"Recipe should not be in favorites anymore"


class TestFavoritesPersistence:
    """Test favorites persistence across requests"""

    @pytest.fixture(scope='class')
    def session(self):
        """Create a session with cookies"""
        return requests.Session()

    @pytest.fixture(scope='class')
    def logged_in_session(self, session):
        """Login and return session"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return session

    def test_favorite_persists_after_second_status_check(self, logged_in_session):
        """Favorite should persist after multiple status checks"""
        # Add favorite
        logged_in_session.post(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")
        
        # Check status multiple times
        for _ in range(3):
            response = logged_in_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite-status")
            assert response.status_code == 200
            assert response.json().get("favorited") == True
        
        # Clean up
        logged_in_session.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/favorite")


class TestFavoritesNonExistentRecipe:
    """Test favorites endpoints with non-existent recipes"""

    @pytest.fixture(scope='class')
    def session(self):
        """Create a session with cookies"""
        return requests.Session()

    @pytest.fixture(scope='class')
    def logged_in_session(self, session):
        """Login and return session"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return session

    def test_add_favorite_nonexistent_recipe(self, logged_in_session):
        """Adding favorite for non-existent recipe should return 404"""
        response = logged_in_session.post(f"{BASE_URL}/api/recipes/this-recipe-does-not-exist-12345/favorite")
        assert response.status_code == 404, f"Expected 404 for non-existent recipe, got {response.status_code}"
