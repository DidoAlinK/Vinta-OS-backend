"""
Integration Tests — Attendance Flow
Tests for check-in/out, PIN attribution, auto-checkout.
"""
import uuid
import pytest
from datetime import time, datetime, timezone, timedelta
from app.extensions import db
from app.models.attendance import SessionStudent
from app.models.audit import ActivityLog


@pytest.mark.integration
class TestCheckInFlow:
    """Test student check-in to session."""

    def test_check_in_student(self, client, auth_headers_owner, session_obj, student):
        """Staff should be able to check in a student to a session."""
        resp = client.post(
            "/api/attendance/check-in",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
                "pin": "1234",
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_present"] is True
        assert data["checked_in_at"] is not None

    def test_check_in_creates_activity_log(self, client, auth_headers_owner, session_obj, student):
        """Check-in should create an activity log entry."""
        client.post(
            "/api/attendance/check-in",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
                "pin": "1234",
            },
            headers=auth_headers_owner,
        )

        log = ActivityLog.query.filter_by(
            entity_type="session",
            entity_id=session_obj.id,
            action="checked_in",
        ).first()
        assert log is not None
        assert log.description is not None
        assert "check-in" in log.description.lower()


@pytest.mark.integration
class TestCheckOutFlow:
    """Test student check-out from session."""

    def _check_in_first(self, client, headers, session_id, student_id):
        """Helper to check in a student first."""
        client.post(
            "/api/attendance/check-in",
            json={
                "session_id": session_id,
                "student_id": student_id,
                "pin": "1234",
            },
            headers=headers,
        )

    def test_check_out_student(self, client, auth_headers_owner, session_obj, student):
        """Staff should be able to check out a checked-in student."""
        self._check_in_first(client, auth_headers_owner, session_obj.id, student.id)

        resp = client.post(
            "/api/attendance/check-out",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["checked_out_at"] is not None

    def test_check_out_without_check_in_fails(self, client, auth_headers_owner, session_obj, student):
        """Cannot check out a student who hasn't checked in."""
        resp = client.post(
            "/api/attendance/check-out",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 404


@pytest.mark.integration
class TestSessionRoster:
    """Test session roster operations."""

    def test_get_empty_roster(self, client, auth_headers_owner, session_obj):
        """New session should have empty roster."""
        resp = client.get(
            f"/api/attendance/roster/{session_obj.id}",
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["roster"] == []

    def test_add_student_to_session(self, client, auth_headers_owner, session_obj, student):
        """Should be able to add a student to a session roster."""
        resp = client.post(
            "/api/attendance/add-to-session",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["student_id"] == student.id
        assert data["is_present"] is False

    def test_duplicate_add_is_idempotent(self, client, auth_headers_owner, session_obj, student):
        """Adding the same student twice should return existing record."""
        client.post(
            "/api/attendance/add-to-session",
            json={"session_id": session_obj.id, "student_id": student.id},
            headers=auth_headers_owner,
        )
        resp = client.post(
            "/api/attendance/add-to-session",
            json={"session_id": session_obj.id, "student_id": student.id},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200  # Returns existing


@pytest.mark.integration
class TestAutoCheckout:
    """Test auto-checkout trigger."""

    def test_auto_checkout_triggers(self, client, auth_headers_owner, session_obj, student):
        """Auto-checkout should check out all present students."""
        # Check in first
        client.post(
            "/api/attendance/check-in",
            json={
                "session_id": session_obj.id,
                "student_id": student.id,
                "pin": "1234",
            },
            headers=auth_headers_owner,
        )

        # Trigger auto-checkout
        resp = client.post(
            "/api/attendance/auto-checkout",
            json={"session_id": session_obj.id},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["checked_out_count"] == 1
