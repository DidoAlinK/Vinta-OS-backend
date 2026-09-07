"""
Unit Tests — PIN Authentication
Tests for PIN hashing, verification, and authentication flows.
"""
import uuid
import pytest
from app.models.user import User
from app.services import auth_service


@pytest.mark.unit
class TestPinHashing:
    """Test PIN hashing and verification."""

    def test_hash_pin_returns_string(self, db):
        """PIN hash should be a string."""
        hashed = User.hash_pin("1234")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_pin_success(self, db):
        """Correct PIN should verify successfully."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test User",
            email="test@test.com",
            role="staff",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        assert user.verify_pin("1234") is True

    def test_verify_pin_failure(self, db):
        """Wrong PIN should fail verification."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test User",
            email="test@test.com",
            role="staff",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        assert user.verify_pin("5678") is False

    def test_set_pin_updates_hash(self, db):
        """set_pin should update the stored hash."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test User",
            email="test@test.com",
            role="staff",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        old_hash = user.pin_hash
        user.set_pin("5678")
        db.session.flush()

        assert user.pin_hash != old_hash
        assert user.verify_pin("5678") is True
        assert user.verify_pin("1234") is False


@pytest.mark.unit
class TestPasswordAuth:
    """Test owner password hashing and verification."""

    def test_hash_password(self, db):
        """Password hash should be generated."""
        hashed = User.hash_password("password123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_success(self, db):
        """Correct password should verify."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test Owner",
            email="owner@test.com",
            role="owner",
            pin_hash=User.hash_pin("1234"),
            password_hash=User.hash_password("password123"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        assert user.verify_password("password123") is True

    def test_verify_password_failure(self, db):
        """Wrong password should fail."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test Owner",
            email="owner@test.com",
            role="owner",
            pin_hash=User.hash_pin("1234"),
            password_hash=User.hash_password("password123"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        assert user.verify_password("wrongpassword") is False

    def test_no_password_returns_false(self, db):
        """Staff without password_hash should return False."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test Staff",
            email="staff@test.com",
            role="staff",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()

        assert user.verify_password("anything") is False


@pytest.mark.unit
class TestRoleChecks:
    """Test role-based access helpers."""

    def test_is_owner(self, db):
        """is_owner should return True for owner role."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test Owner",
            email="owner@test.com",
            role="owner",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        assert user.is_owner is True

    def test_is_not_owner_for_staff(self, db):
        """is_owner should return False for staff role."""
        user = User(
            id=str(uuid.uuid4()),
            academy_id="test-academy",
            name="Test Staff",
            email="staff@test.com",
            role="staff",
            pin_hash=User.hash_pin("1234"),
            is_active=True,
        )
        assert user.is_owner is False
