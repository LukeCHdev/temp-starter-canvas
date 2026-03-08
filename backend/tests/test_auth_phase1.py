"""
Phase 1 Auth Testing - Complete Authentication Flow
Tests: Registration, Login, Logout, Session Persistence, Rate Limiting, Password Reset
"""

import pytest
import requests
import os
import uuid
import time

# Use the public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://mongo-link-verify.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test user credentials - unique per run to avoid conflicts
TEST_EMAIL = f"test_auth_{uuid.uuid4().hex[:8]}@test.com"
TEST_USERNAME = f"testuser_{uuid.uuid4().hex[:8]}"
TEST_PASSWORD = "TestPass123"

# Store session for authenticated tests
session = requests.Session()


class TestAuthRegistration:
    """Test user registration endpoint"""
    
    def test_register_new_user_success(self):
        """POST /api/auth/register - Creates user with valid data"""
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") is True
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL.lower()
        assert data["user"]["username"] == TEST_USERNAME.lower()
        assert "user_id" in data["user"]
        
        # Verify sensitive fields are NOT exposed
        assert "password_hash" not in data["user"]
        assert "verification_token" not in data["user"]
        assert "reset_token" not in data["user"]
        
        print(f"✓ Registration successful for {TEST_EMAIL}")
    
    def test_register_duplicate_email_fails(self):
        """POST /api/auth/register - Rejects duplicate email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "username": f"other_{uuid.uuid4().hex[:8]}",
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD
        })
        
        assert response.status_code == 400
        assert "already" in response.json().get("detail", "").lower()
        print("✓ Duplicate email correctly rejected")
    
    def test_register_duplicate_username_fails(self):
        """POST /api/auth/register - Rejects duplicate username"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"other_{uuid.uuid4().hex[:8]}@test.com",
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "confirm_password": TEST_PASSWORD
        })
        
        assert response.status_code == 400
        assert "already" in response.json().get("detail", "").lower() or "taken" in response.json().get("detail", "").lower()
        print("✓ Duplicate username correctly rejected")
    
    def test_register_password_mismatch_fails(self):
        """POST /api/auth/register - Rejects mismatched passwords"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"mismatch_{uuid.uuid4().hex[:8]}@test.com",
            "username": f"mismatch_{uuid.uuid4().hex[:8]}",
            "password": TEST_PASSWORD,
            "confirm_password": "DifferentPass123"
        })
        
        assert response.status_code == 400
        assert "match" in response.json().get("detail", "").lower()
        print("✓ Password mismatch correctly rejected")


class TestAuthLogin:
    """Test user login endpoint"""
    
    def test_login_success(self):
        """POST /api/auth/login - Returns success with session cookie"""
        # Create a fresh session for login
        login_session = requests.Session()
        
        response = login_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert data.get("success") is True
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL.lower()
        
        # Verify sensitive fields not exposed in login response
        assert "password_hash" not in data["user"]
        assert "verification_token" not in data["user"]
        assert "reset_token" not in data["user"]
        
        # Verify cookie is set
        assert "session_token" in login_session.cookies or any("session" in c.name.lower() for c in login_session.cookies)
        
        print("✓ Login successful with session cookie")
        
        # Store session for later tests
        global session
        session = login_session
    
    def test_login_wrong_password_generic_error(self):
        """POST /api/auth/login - Returns generic error for wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "WrongPassword123"
        })
        
        assert response.status_code == 401
        error_msg = response.json().get("detail", "").lower()
        # Should NOT reveal whether email exists - generic message
        assert "invalid" in error_msg or "email or password" in error_msg
        print("✓ Wrong password returns generic error (no user enumeration)")
    
    def test_login_nonexistent_email_generic_error(self):
        """POST /api/auth/login - Returns same generic error for non-existent email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent_user_xyz@test.com",
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 401
        error_msg = response.json().get("detail", "").lower()
        # Must be same generic message to prevent user enumeration
        assert "invalid" in error_msg or "email or password" in error_msg
        print("✓ Non-existent email returns generic error (no user enumeration)")


class TestAuthSession:
    """Test session persistence and /me endpoint"""
    
    def test_get_me_authenticated(self):
        """GET /api/auth/me - Returns user when authenticated"""
        response = session.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        data = response.json()
        
        assert data.get("success") is True
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL.lower()
        
        # Verify sensitive fields NOT exposed
        user = data["user"]
        assert "password_hash" not in user
        assert "verification_token" not in user
        assert "reset_token" not in user
        
        print("✓ GET /me returns authenticated user without sensitive fields")
    
    def test_get_me_unauthenticated(self):
        """GET /api/auth/me - Returns 401 when not authenticated"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401
        print("✓ GET /me returns 401 when not authenticated")
    
    def test_session_persists_across_requests(self):
        """Session cookie persists across multiple requests"""
        # Make multiple requests with same session
        for i in range(3):
            response = session.get(f"{BASE_URL}/api/auth/me")
            assert response.status_code == 200
            assert response.json().get("user", {}).get("email") == TEST_EMAIL.lower()
        
        print("✓ Session persists across multiple requests")


class TestAuthProtectedEndpoints:
    """Test protected endpoints require authentication"""
    
    def test_review_without_auth_returns_401(self):
        """POST /api/recipes/{slug}/review - Returns 401 without auth"""
        response = requests.post(
            f"{BASE_URL}/api/recipes/spaghetti-alla-carbonara-italy/review",
            json={"rating": 5, "comment": "Great recipe!"}
        )
        
        assert response.status_code == 401
        print("✓ Review submission without auth returns 401")


class TestAuthLogout:
    """Test logout functionality"""
    
    def test_logout_clears_session(self):
        """POST /api/auth/logout - Clears session"""
        # First verify we're logged in
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 200
        
        # Logout
        logout_response = session.post(f"{BASE_URL}/api/auth/logout")
        assert logout_response.status_code == 200
        assert logout_response.json().get("success") is True
        
        # Verify session is cleared - /me should now return 401
        me_after = session.get(f"{BASE_URL}/api/auth/me")
        assert me_after.status_code == 401
        
        print("✓ Logout clears session successfully")


class TestPasswordReset:
    """Test password reset flow (DEV MODE - tokens logged to console)"""
    
    def test_request_password_reset(self):
        """POST /api/auth/reset-password - Logs token to server logs"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "email": TEST_EMAIL
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # Message should NOT reveal if email exists (anti-enumeration)
        assert "if an account exists" in data.get("message", "").lower() or "reset" in data.get("message", "").lower()
        
        print("✓ Password reset request returns success (token logged to server)")
    
    def test_request_reset_nonexistent_email_same_response(self):
        """POST /api/auth/reset-password - Same response for non-existent email"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password", json={
            "email": "nonexistent_user_xyz123@test.com"
        })
        
        # Should return same success response to prevent enumeration
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        print("✓ Non-existent email returns same response (no enumeration)")
    
    def test_reset_password_confirm_invalid_token(self):
        """POST /api/auth/reset-password/confirm - Rejects invalid token"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password/confirm", json={
            "token": "invalid_token_xyz",
            "new_password": "NewPassword123",
            "confirm_password": "NewPassword123"
        })
        
        assert response.status_code == 400
        assert "invalid" in response.json().get("detail", "").lower() or "expired" in response.json().get("detail", "").lower()
        
        print("✓ Invalid reset token correctly rejected")
    
    def test_reset_password_confirm_password_mismatch(self):
        """POST /api/auth/reset-password/confirm - Rejects password mismatch"""
        response = requests.post(f"{BASE_URL}/api/auth/reset-password/confirm", json={
            "token": "some_token",
            "new_password": "NewPassword123",
            "confirm_password": "DifferentPassword123"
        })
        
        assert response.status_code == 400
        assert "match" in response.json().get("detail", "").lower() or "invalid" in response.json().get("detail", "").lower()
        
        print("✓ Password mismatch in reset correctly rejected")


class TestGoogleOAuth:
    """Test Google OAuth endpoint (redirect URL only)"""
    
    def test_google_auth_endpoint_exists(self):
        """POST /api/auth/social/google - Endpoint exists"""
        # We can't fully test OAuth, but we can verify the endpoint exists
        response = requests.post(f"{BASE_URL}/api/auth/social/google", json={
            "session_id": "test_invalid_session"
        })
        
        # Should return 401 (invalid session) not 404 (endpoint missing)
        assert response.status_code in [401, 500], f"Unexpected status: {response.status_code}"
        print("✓ Google OAuth endpoint exists")


class TestRateLimiting:
    """Test login rate limiting - 10 attempts per 5 minutes per IP
    
    NOTE: Run these tests LAST as they may block the IP for 5 minutes.
    All preview requests share the same proxy IP.
    """
    
    @pytest.mark.order("last")
    def test_rate_limit_after_many_attempts(self):
        """POST /api/auth/login - Returns 429 after too many failed attempts"""
        # Make 11 failed login attempts (limit is 10)
        for i in range(11):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": f"rate_limit_test_{i}@test.com",
                "password": "wrong_password"
            })
            
            if response.status_code == 429:
                print(f"✓ Rate limit triggered after {i+1} attempts")
                return
            
            time.sleep(0.1)  # Small delay between requests
        
        # If we got here, check the last response
        assert response.status_code == 429, f"Expected 429 rate limit, got {response.status_code}"
        print("✓ Rate limiting working correctly")


# Run tests in order
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
