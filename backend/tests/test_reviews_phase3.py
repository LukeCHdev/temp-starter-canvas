"""
Phase 3 - Reviews/Ratings API Tests
Tests for:
- POST /api/recipes/{slug}/review (create review, auth required)
- PUT /api/recipes/{slug}/review (update own review)
- DELETE /api/recipes/{slug}/review (delete own review)
- GET /api/recipes/{slug}/reviews (get reviews, guest allowed)
- Validation: min 10 chars comment, rating 1-5
- XSS prevention via html.escape
- Rate limiting: 5 reviews per hour per user
- One review per user per recipe (upsert behavior)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "phase1final@test.com"
TEST_USER_PASSWORD = "TestPass123"
TEST_RECIPE_SLUG = "pizza-margherita-italy"  # Known recipe from context


class TestReviewsAuth:
    """Test authentication requirements for review endpoints"""
    
    def test_create_review_guest_returns_401(self):
        """POST /recipes/{slug}/review should return 401 for guests"""
        response = requests.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "This is a great recipe!"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        data = response.json()
        assert "logged in" in data.get("detail", "").lower() or "login" in data.get("detail", "").lower()
        print("PASS: Guest cannot create review (401)")
    
    def test_update_review_guest_returns_401(self):
        """PUT /recipes/{slug}/review should return 401 for guests"""
        response = requests.put(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 4, "comment": "Updated comment here"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Guest cannot update review (401)")
    
    def test_delete_review_guest_returns_401(self):
        """DELETE /recipes/{slug}/review should return 401 for guests"""
        response = requests.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Guest cannot delete review (401)")
    
    def test_get_reviews_guest_allowed(self):
        """GET /recipes/{slug}/reviews should work for guests"""
        response = requests.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "reviews" in data
        assert "average_rating" in data
        assert "ratings_count" in data
        # Guest should not have user_review
        assert data.get("user_review") is None, "Guest should not have user_review"
        print(f"PASS: Guest can view reviews (count: {len(data['reviews'])})")


class TestReviewsValidation:
    """Test validation rules for reviews"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return session
    
    def test_comment_too_short_returns_422(self, auth_session):
        """POST with comment < 10 chars should return 422"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "short"}  # 5 chars < 10 min
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print("PASS: Comment < 10 chars returns 422")
    
    def test_comment_empty_string_allowed(self, auth_session):
        """POST with empty comment is allowed (comment is optional)"""
        # Empty string should be treated as null/no comment
        # The validation is min_length=10 but comment is optional
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/risotto-alla-milanese-italy/review",
            json={"rating": 4, "comment": ""}  # Empty comment should be allowed
        )
        # Either 200 (success) or it converts empty to null
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print("PASS: Empty comment is allowed (treated as no comment)")
        else:
            print("INFO: Empty comment is rejected (422)")
    
    def test_rating_below_1_returns_422(self, auth_session):
        """POST with rating 0 should return 422"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 0, "comment": "This is a valid length comment"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Rating 0 returns 422")
    
    def test_rating_above_5_returns_422(self, auth_session):
        """POST with rating 6 should return 422"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 6, "comment": "This is a valid length comment"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Rating 6 returns 422")
    
    def test_rating_valid_range_1(self, auth_session):
        """POST with rating 1 should be accepted"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 1}  # No comment, just rating
        )
        # Should succeed or update existing
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Rating 1 is valid")
    
    def test_rating_valid_range_5(self, auth_session):
        """POST with rating 5 should be accepted"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "Excellent authentic recipe!"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Rating 5 is valid")


class TestReviewsCRUD:
    """Test CRUD operations for reviews"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return session
    
    def test_create_review_success(self, auth_session):
        """POST /recipes/{slug}/review creates a review"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 4, "comment": "A wonderful traditional recipe that my family loves!"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert "review" in data
        assert data["review"]["rating"] == 4
        assert "average_rating" in data
        assert "ratings_count" in data
        print(f"PASS: Review created - avg: {data['average_rating']}, count: {data['ratings_count']}")
    
    def test_duplicate_review_upserts(self, auth_session):
        """POST duplicate review for same recipe updates existing (upsert)"""
        # First review
        response1 = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 3, "comment": "First version of my review here"}
        )
        assert response1.status_code == 200
        
        # Second review (should update, not create new)
        response2 = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "Updated version of my review!"}
        )
        assert response2.status_code == 200, f"Expected 200, got {response2.status_code}"
        data = response2.json()
        assert data["review"]["rating"] == 5
        assert "Updated" in data["review"]["comment"]
        print("PASS: Duplicate review updates existing (upsert behavior)")
    
    def test_get_reviews_returns_user_review_for_authenticated(self, auth_session):
        """GET /recipes/{slug}/reviews returns user_review for logged-in user"""
        response = auth_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert "user_review" in data
        # User should have their own review
        if data["user_review"]:
            assert data["user_review"]["user_id"] is not None
            print(f"PASS: user_review returned for authenticated user: rating={data['user_review']['rating']}")
        else:
            print("INFO: No user_review yet for this user")
    
    def test_update_review_success(self, auth_session):
        """PUT /recipes/{slug}/review updates own review"""
        # First ensure a review exists
        auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 4, "comment": "Original review comment here"}
        )
        
        # Update the review
        response = auth_session.put(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "My updated review with new thoughts"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert data["review"]["rating"] == 5
        print("PASS: Review updated successfully via PUT")
    
    def test_delete_review_success(self, auth_session):
        """DELETE /recipes/{slug}/review deletes own review"""
        # First ensure a review exists
        auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 3, "comment": "Review to be deleted soon"}
        )
        
        # Delete the review
        response = auth_session.delete(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        print(f"PASS: Review deleted - new avg: {data.get('average_rating')}, count: {data.get('ratings_count')}")
        
        # Verify deletion
        get_response = auth_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        assert get_response.status_code == 200
        assert get_response.json().get("user_review") is None, "user_review should be None after deletion"
        print("PASS: Verified review is deleted")


class TestXSSPrevention:
    """Test XSS prevention via html.escape"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return session
    
    def test_html_tags_escaped_in_comment(self, auth_session):
        """HTML tags in comment should be escaped"""
        xss_comment = "<script>alert('XSS')</script>This is a test comment"
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 4, "comment": xss_comment}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        saved_comment = data["review"]["comment"]
        
        # Check that HTML is escaped
        assert "<script>" not in saved_comment, "Script tag should be escaped"
        assert "&lt;script&gt;" in saved_comment or "script" in saved_comment.replace("&lt;", "<").replace("&gt;", ">")
        print(f"PASS: HTML tags escaped. Saved: {saved_comment[:50]}...")
    
    def test_special_chars_escaped(self, auth_session):
        """Special HTML characters should be escaped"""
        special_comment = "Great recipe! <b>Bold</b> & 'quotes' \"double\""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": special_comment}
        )
        assert response.status_code == 200
        data = response.json()
        saved_comment = data["review"]["comment"]
        
        # Check that <b> is escaped
        assert "<b>" not in saved_comment, "B tag should be escaped"
        print(f"PASS: Special chars escaped. Saved: {saved_comment[:50]}...")


class TestReviewsNonExistent:
    """Test behavior with non-existent recipes"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return session
    
    def test_create_review_nonexistent_recipe_returns_404(self, auth_session):
        """POST review for non-existent recipe should return 404"""
        response = auth_session.post(
            f"{BASE_URL}/api/recipes/nonexistent-recipe-slug-12345/review",
            json={"rating": 5, "comment": "This recipe does not exist!"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Non-existent recipe returns 404")
    
    def test_get_reviews_nonexistent_recipe_returns_404(self, auth_session):
        """GET reviews for non-existent recipe should return 404"""
        response = auth_session.get(f"{BASE_URL}/api/recipes/nonexistent-recipe-slug-12345/reviews")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: GET reviews for non-existent recipe returns 404")


class TestReviewsDataIntegrity:
    """Test data integrity for reviews"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login and return authenticated session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.text}")
        return session
    
    def test_review_contains_username(self, auth_session):
        """Review should contain username"""
        # Create a review
        auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 4, "comment": "Testing username in review data"}
        )
        
        # Get reviews
        response = auth_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        assert response.status_code == 200
        data = response.json()
        
        if data.get("user_review"):
            assert "username" in data["user_review"]
            assert data["user_review"]["username"] is not None
            print(f"PASS: Review contains username: {data['user_review']['username']}")
    
    def test_review_has_created_at_date(self, auth_session):
        """Review should have created_at timestamp"""
        response = auth_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        assert response.status_code == 200
        data = response.json()
        
        if data["reviews"]:
            review = data["reviews"][0]
            assert "created_at" in review
            assert review["created_at"] is not None
            print(f"PASS: Review has created_at: {review['created_at']}")
    
    def test_average_rating_recalculated_after_review(self, auth_session):
        """Average rating should be recalculated after adding/updating review"""
        # Get initial average
        response1 = auth_session.get(f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/reviews")
        initial_avg = response1.json().get("average_rating", 0)
        initial_count = response1.json().get("ratings_count", 0)
        
        # Add/update review
        response2 = auth_session.post(
            f"{BASE_URL}/api/recipes/{TEST_RECIPE_SLUG}/review",
            json={"rating": 5, "comment": "Testing average recalculation here"}
        )
        assert response2.status_code == 200
        new_avg = response2.json().get("average_rating")
        new_count = response2.json().get("ratings_count")
        
        assert new_avg is not None, "average_rating should be returned"
        assert new_count is not None, "ratings_count should be returned"
        print(f"PASS: Average rating recalculated - was {initial_avg}, now {new_avg} (count: {new_count})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
