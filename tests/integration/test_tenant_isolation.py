"""
Integration Tests — Tenant Isolation
Verifies that academy A cannot access academy B's data.
"""
import uuid
import pytest
from app.extensions import db
from app.models.academy import Academy, AcademySettings, Subscription
from app.models.user import User
from app.models.student import Student


@pytest.mark.integration
class TestTenantIsolation:
    """Ensure cross-academy access is blocked."""

    def _create_second_academy(self, db):
        """Helper to create a second academy for cross-tenant testing."""
        academy2 = Academy(
            id=str(uuid.uuid4()),
            name="Other Academy",
            email="other@academy.com",
        )
        db.session.add(academy2)
        settings = AcademySettings(academy_id=academy2.id)
        db.session.add(settings)
        sub = Subscription(academy_id=academy2.id, tier="starter", status="active")
        db.session.add(sub)

        owner2 = User(
            id=str(uuid.uuid4()),
            academy_id=academy2.id,
            name="Other Owner",
            email="other@owner.com",
            role="owner",
            pin_hash=User.hash_pin("1111"),
            password_hash=User.hash_password("otherpass"),
            is_active=True,
        )
        db.session.add(owner2)
        db.session.flush()
        return academy2, owner2

    def test_cannot_list_other_academy_students(self, client, academy, owner):
        """Student list should only return students from the authenticated academy."""
        academy2, owner2 = self._create_second_academy(db)

        # Login as academy 1 owner
        resp = client.post("/api/auth/login", json={
            "email": "owner@test.com",
            "password": "password123",
        })
        token = resp.get_json()["access_token"]

        # Try to list with wrong academy ID
        resp = client.get(
            "/api/students",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Academy-Id": academy2.id,
            },
        )
        assert resp.status_code == 403

    def test_same_academy_access_allowed(self, client, academy, owner, auth_headers_owner):
        """Students should be accessible with correct academy header."""
        resp = client.get(
            "/api/students",
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200

    def test_missing_academy_header_returns_400(self, client, owner):
        """Request without X-Academy-Id should return 400."""
        resp = client.post("/api/auth/login", json={
            "email": "owner@test.com",
            "password": "password123",
        })
        token = resp.get_json()["access_token"]

        resp = client.get(
            "/api/students",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


@pytest.mark.integration
class TestAuthentication:
    """Test authentication flows."""

    def test_login_success(self, client, owner):
        """Valid credentials should return tokens."""
        resp = client.post("/api/auth/login", json={
            "email": "owner@test.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["role"] == "owner"

    def test_login_invalid_password(self, client, owner):
        """Wrong password should return 401."""
        resp = client.post("/api/auth/login", json={
            "email": "owner@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client, owner):
        """Non-existent email should return 401."""
        resp = client.post("/api/auth/login", json={
            "email": "nobody@test.com",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_verify_pin_success(self, client, owner, staff):
        """Valid PIN should return access token."""
        resp = client.post("/api/auth/verify-pin", json={
            "user_id": staff.id,
            "pin": "5678",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "access_token" in data
        assert data["role"] == "staff"

    def test_verify_pin_invalid(self, client, owner, staff):
        """Invalid PIN should return 401."""
        resp = client.post("/api/auth/verify-pin", json={
            "user_id": staff.id,
            "pin": "0000",
        })
        assert resp.status_code == 401

    def test_protected_route_without_token(self, client, academy):
        """Protected routes should require JWT token."""
        resp = client.get("/api/students")
        assert resp.status_code in (401, 422)
