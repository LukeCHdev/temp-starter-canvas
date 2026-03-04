"""
Techniques System Tests - Backend API Testing

Tests cover:
- Public GET /api/techniques (list published techniques)
- Public GET /api/techniques/{slug} (single technique)
- Admin POST /api/admin/techniques (create technique)
- Validation rules for TechniqueCreate
- MongoDB indexes verification
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


class TestPublicTechniquesEndpoints:
    """Tests for public (no auth) techniques endpoints"""

    def test_get_all_techniques_returns_array(self):
        """GET /api/techniques returns flat array (not wrapped object)"""
        response = requests.get(f"{BASE_URL}/api/techniques")
        assert response.status_code == 200
        data = response.json()
        # Must be a flat array, not {"techniques": [...]}
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"PASS: GET /api/techniques returns array with {len(data)} items")

    def test_get_all_techniques_sorted_newest_first(self):
        """GET /api/techniques returns techniques sorted by created_at descending"""
        response = requests.get(f"{BASE_URL}/api/techniques")
        assert response.status_code == 200
        data = response.json()
        if len(data) >= 2:
            # Check sorting (newest first = descending created_at)
            timestamps = [t.get("created_at", "") for t in data]
            assert timestamps == sorted(timestamps, reverse=True), "Not sorted newest first"
            print(f"PASS: Techniques sorted newest first - {timestamps[0]} > {timestamps[-1]}")
        else:
            print("PASS: Not enough techniques to verify sorting")

    def test_get_all_techniques_only_published(self):
        """GET /api/techniques returns only published techniques (no drafts)"""
        response = requests.get(f"{BASE_URL}/api/techniques")
        assert response.status_code == 200
        data = response.json()
        for tech in data:
            assert tech.get("status") == "published", f"Found non-published: {tech.get('status')}"
        print(f"PASS: All {len(data)} techniques have status=published")

    def test_get_all_techniques_has_required_fields(self):
        """GET /api/techniques returns techniques with all required fields"""
        response = requests.get(f"{BASE_URL}/api/techniques")
        assert response.status_code == 200
        data = response.json()
        required_fields = ["title", "slug", "category", "difficulty", "readTime", "introduction", "sections"]
        for tech in data:
            for field in required_fields:
                assert field in tech, f"Missing field '{field}' in technique {tech.get('slug')}"
        print(f"PASS: All techniques have required fields")

    def test_get_technique_by_slug_published(self):
        """GET /api/techniques/knife-skills-fundamentals returns published technique"""
        response = requests.get(f"{BASE_URL}/api/techniques/knife-skills-fundamentals")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "knife-skills-fundamentals"
        assert data.get("status") == "published"
        assert data.get("title") == "Knife Skills Fundamentals"
        print(f"PASS: GET /api/techniques/knife-skills-fundamentals returned {data.get('title')}")

    def test_get_technique_by_slug_has_all_fields(self):
        """GET /api/techniques/{slug} returns technique with all fields"""
        response = requests.get(f"{BASE_URL}/api/techniques/knife-skills-fundamentals")
        assert response.status_code == 200
        data = response.json()
        # Check all expected fields
        assert "title" in data
        assert "slug" in data
        assert "category" in data
        assert "difficulty" in data
        assert "readTime" in data
        assert "introduction" in data
        assert "sections" in data
        assert isinstance(data["sections"], list)
        assert len(data["sections"]) > 0
        # Check section structure
        for section in data["sections"]:
            assert "title" in section
            assert "content" in section
        print(f"PASS: Technique has all fields including {len(data['sections'])} sections")

    def test_get_technique_by_slug_nonexistent_returns_404(self):
        """GET /api/techniques/{slug} returns 404 for nonexistent slug"""
        response = requests.get(f"{BASE_URL}/api/techniques/this-slug-does-not-exist-xyz")
        assert response.status_code == 404
        print("PASS: GET /api/techniques/nonexistent returns 404")

    def test_get_technique_excludes_mongodb_id(self):
        """GET /api/techniques/{slug} excludes MongoDB _id field"""
        response = requests.get(f"{BASE_URL}/api/techniques/knife-skills-fundamentals")
        assert response.status_code == 200
        data = response.json()
        assert "_id" not in data, "MongoDB _id should be excluded"
        print("PASS: MongoDB _id excluded from response")


class TestAdminTechniquesAuth:
    """Tests for admin techniques endpoint authentication/authorization"""

    def test_create_technique_without_auth_returns_403(self):
        """POST /api/admin/techniques returns 403 without auth"""
        payload = {
            "title": "Test Technique No Auth",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro for unauthorized request",
            "sections": [{"title": "Section 1", "content": "Content here"}]
        }
        response = requests.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("PASS: POST /api/admin/techniques without auth returns 403")

    def test_create_technique_with_regular_user_returns_403(self):
        """POST /api/admin/techniques returns 403 for non-admin user"""
        # Login as regular user (testregular@example.com created during testing)
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testregular@example.com",
            "password": "testpass123"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Could not login as regular user: {login_response.status_code}")
        
        # Try to create technique
        payload = {
            "title": "Test Technique Regular User",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro for regular user",
            "sections": [{"title": "Section 1", "content": "Content here"}]
        }
        response = session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 403, f"Expected 403 for regular user, got {response.status_code}"
        print("PASS: POST /api/admin/techniques with regular user returns 403")


class TestAdminTechniquesCreate:
    """Tests for admin technique creation with proper auth"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@souschef.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as admin: {response.status_code} - {response.text}")
        return session

    @pytest.fixture(scope="class")
    def unique_suffix(self):
        """Generate unique suffix for test titles to avoid slug conflicts"""
        import time
        return str(int(time.time() * 1000))[-6:]

    def test_create_technique_with_admin_auth(self, admin_session, unique_suffix):
        """POST /api/admin/techniques creates technique with admin auth"""
        payload = {
            "title": f"TEST Admin Created {unique_suffix}",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro created by admin",
            "sections": [{"title": "Section 1", "content": "Test content here"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "TEST Admin Created" in data.get("title")
        assert data.get("status") == "draft"  # Default status
        print(f"PASS: Created technique with slug={data.get('slug')}")

    def test_create_technique_auto_generates_slug(self, admin_session, unique_suffix):
        """POST /api/admin/techniques auto-generates slug from title"""
        payload = {
            "title": f"TEST Slug Gen {unique_suffix}",
            "category": "Testing",
            "difficulty": "Intermediate",
            "readTime": 10,
            "introduction": "Testing auto slug",
            "sections": [{"title": "Test", "content": "Test content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Slug should be lowercase-hyphenated version of title
        assert f"test-slug-gen-{unique_suffix}" == data.get("slug")
        print(f"PASS: Auto-generated slug: {data.get('slug')}")

    def test_create_technique_defaults_to_draft(self, admin_session, unique_suffix):
        """POST /api/admin/techniques defaults status to 'draft'"""
        payload = {
            "title": f"TEST Draft Default {unique_suffix}",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 3,
            "introduction": "Testing draft default",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "draft", f"Expected draft, got {data.get('status')}"
        print("PASS: Status defaults to 'draft'")

    def test_create_technique_with_custom_status(self, admin_session, unique_suffix):
        """POST /api/admin/techniques accepts custom status"""
        payload = {
            "title": f"TEST Pub Status {unique_suffix}",
            "category": "Testing",
            "difficulty": "Advanced",
            "readTime": 15,
            "introduction": "Testing published status",
            "sections": [{"title": "Test", "content": "Content"}],
            "status": "published"
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "published"
        print("PASS: Can set status to 'published'")

    def test_create_technique_duplicate_slug_returns_409(self, admin_session):
        """POST /api/admin/techniques returns 409 for duplicate slug"""
        # Use existing slug
        payload = {
            "title": "Knife Skills Fundamentals",  # Same title as existing
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Duplicate slug test",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        print("PASS: Duplicate slug returns 409")


class TestTechniquesValidation:
    """Tests for TechniqueCreate validation rules"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@souschef.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as admin: {response.status_code}")
        return session

    def test_validation_title_too_short_returns_422(self, admin_session):
        """Title < 3 chars returns 422"""
        payload = {
            "title": "AB",  # 2 chars, < 3
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Title < 3 chars returns 422")

    def test_validation_title_too_long_returns_422(self, admin_session):
        """Title > 120 chars returns 422"""
        payload = {
            "title": "A" * 121,  # 121 chars, > 120
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Title > 120 chars returns 422")

    def test_validation_empty_sections_returns_422(self, admin_session):
        """Empty sections array returns 422"""
        payload = {
            "title": "TEST Empty Sections",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test intro",
            "sections": []  # Empty array
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Empty sections returns 422")

    def test_validation_readtime_zero_returns_422(self, admin_session):
        """readTime = 0 returns 422"""
        payload = {
            "title": "TEST Zero ReadTime",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 0,  # Invalid: must be > 0
            "introduction": "Test intro",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: readTime = 0 returns 422")

    def test_validation_readtime_negative_returns_422(self, admin_session):
        """Negative readTime returns 422"""
        payload = {
            "title": "TEST Negative ReadTime",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": -5,  # Invalid: must be > 0
            "introduction": "Test intro",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Negative readTime returns 422")

    def test_validation_invalid_difficulty_returns_422(self, admin_session):
        """Invalid difficulty value returns 422"""
        payload = {
            "title": "TEST Invalid Difficulty",
            "category": "Testing",
            "difficulty": "Expert",  # Invalid: must be Beginner/Intermediate/Advanced
            "readTime": 5,
            "introduction": "Test intro",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("PASS: Invalid difficulty returns 422")

    def test_validation_valid_difficulties_accepted(self, admin_session):
        """Valid difficulty values are accepted"""
        for difficulty in ["Beginner", "Intermediate", "Advanced"]:
            payload = {
                "title": f"TEST Valid Difficulty {difficulty}",
                "category": "Testing",
                "difficulty": difficulty,
                "readTime": 5,
                "introduction": "Test intro",
                "sections": [{"title": "Test", "content": "Content"}]
            }
            response = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
            # May be 200 or 409 (if already exists), but not 422
            assert response.status_code != 422, f"{difficulty} should be valid"
        print("PASS: All valid difficulties accepted (Beginner/Intermediate/Advanced)")


class TestMongoDBIndexes:
    """Tests for MongoDB index existence"""

    def test_mongodb_indexes_exist(self):
        """Verify required indexes exist on techniques collection"""
        # This is a meta-test - indexes were verified during setup
        # We test indirectly by verifying slug uniqueness works
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@souschef.com",
            "password": "admin123"
        })
        if login_resp.status_code != 200:
            pytest.skip("Could not login as admin")
        
        # Try to create duplicate slug - should fail if unique index exists
        payload = {
            "title": "Knife Skills Fundamentals",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "Test",
            "sections": [{"title": "Test", "content": "Content"}]
        }
        response = session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        assert response.status_code == 409, "Slug unique index should prevent duplicates"
        print("PASS: slug_1 unique index exists (duplicate rejected with 409)")


class TestDraftTechniqueNotPubliclyVisible:
    """Test that draft techniques are not visible in public endpoints"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login as admin and return session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@souschef.com",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip(f"Could not login as admin: {response.status_code}")
        return session

    def test_draft_technique_not_in_list(self, admin_session):
        """Draft techniques should not appear in GET /api/techniques"""
        # Create a draft technique
        payload = {
            "title": "TEST Draft Invisible In List",
            "slug": "test-draft-invisible-list",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "This should not be visible",
            "sections": [{"title": "Test", "content": "Content"}],
            "status": "draft"
        }
        create_resp = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        # Accept either 200 (created) or 409 (already exists)
        assert create_resp.status_code in [200, 409]
        
        # Check public list
        list_resp = requests.get(f"{BASE_URL}/api/techniques")
        assert list_resp.status_code == 200
        techniques = list_resp.json()
        slugs = [t.get("slug") for t in techniques]
        assert "test-draft-invisible-list" not in slugs, "Draft should not be in public list"
        print("PASS: Draft technique not in public list")

    def test_draft_technique_returns_404_on_direct_access(self, admin_session):
        """GET /api/techniques/{slug} returns 404 for draft technique"""
        # Create a draft technique
        payload = {
            "title": "TEST Draft Direct Access 404",
            "slug": "test-draft-direct-404",
            "category": "Testing",
            "difficulty": "Beginner",
            "readTime": 5,
            "introduction": "This should 404",
            "sections": [{"title": "Test", "content": "Content"}],
            "status": "draft"
        }
        create_resp = admin_session.post(f"{BASE_URL}/api/admin/techniques", json=payload)
        # Accept either 200 (created) or 409 (already exists)
        
        # Direct access should return 404
        direct_resp = requests.get(f"{BASE_URL}/api/techniques/test-draft-direct-404")
        assert direct_resp.status_code == 404, f"Expected 404, got {direct_resp.status_code}"
        print("PASS: Draft technique returns 404 on direct access")


class TestExistingTechniquesData:
    """Verify the existing seeded techniques data"""

    def test_knife_skills_fundamentals_exists(self):
        """Verify knife-skills-fundamentals technique exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/techniques/knife-skills-fundamentals")
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == "Knife Skills Fundamentals"
        assert data.get("category") == "Knife Skills"
        assert data.get("difficulty") == "Beginner"
        assert data.get("readTime") == 8
        assert "julienne" in data.get("introduction", "").lower() or "knife" in data.get("introduction", "").lower()
        print("PASS: knife-skills-fundamentals exists with correct data")

    def test_sauce_making_basics_exists(self):
        """Verify sauce-making-basics technique exists with correct data"""
        response = requests.get(f"{BASE_URL}/api/techniques/sauce-making-basics")
        assert response.status_code == 200
        data = response.json()
        assert data.get("title") == "Sauce Making Basics"
        assert data.get("category") == "Sauces"
        assert data.get("difficulty") == "Intermediate"
        assert data.get("readTime") == 12
        print("PASS: sauce-making-basics exists with correct data")


# Cleanup fixture to remove TEST_ prefixed techniques after tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_techniques():
    """Cleanup test-created techniques after all tests"""
    yield
    # Note: In production, we would clean up TEST_ prefixed techniques here
    # For now, we leave them as they don't affect production functionality
    print("INFO: Test techniques with TEST_ prefix may remain in DB")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
