"""
Integration Tests — Calendar Drag & Drop
Tests for session creation, move, resize via API.
"""
import uuid
import pytest
from datetime import date, time, timedelta
from app.extensions import db
from app.models.scheduling import Session


@pytest.mark.integration
class TestSessionCRUD:
    """Test session create/read/update/delete via API."""

    def test_create_session(self, client, auth_headers_owner, class_obj, teacher):
        """Should create a new session with valid data."""
        resp = client.post(
            "/api/sessions",
            json={
                "class_id": class_obj.id,
                "date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
                "teacher_id": teacher.id,
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["date"] == date.today().isoformat()
        assert data["start_time"] == "10:00"
        assert data["end_time"] == "11:00"
        assert data["subject"] == "Math"

    def test_create_session_snaps_to_5min(self, client, auth_headers_owner, class_obj, teacher):
        """Session times should snap to 5-minute grid."""
        resp = client.post(
            "/api/sessions",
            json={
                "class_id": class_obj.id,
                "date": date.today().isoformat(),
                "start_time": "10:03",  # Should snap to 10:00
                "end_time": "11:07",    # Should snap to 11:05
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["start_time"] == "10:00"
        assert data["end_time"] == "11:05"

    def test_create_session_missing_fields(self, client, auth_headers_owner):
        """Should return 400 for missing required fields."""
        resp = client.post(
            "/api/sessions",
            json={"class_id": "some-id"},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 400

    def test_get_week_sessions(self, client, auth_headers_owner, session_obj):
        """Should return sessions for the current week."""
        resp = client.get(
            "/api/calendar/week",
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "sessions" in data
        assert "week_start" in data

    def test_get_day_sessions(self, client, auth_headers_owner, session_obj):
        """Should return sessions for a specific day."""
        resp = client.get(
            f"/api/calendar/day?date={date.today().isoformat()}",
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["sessions"]) >= 1


@pytest.mark.integration
class TestSessionDragMove:
    """Test drag-to-move: updating session date and start_time."""

    def test_move_session_to_different_time(self, client, auth_headers_owner, session_obj):
        """Should update session start_time via PATCH."""
        resp = client.patch(
            f"/api/sessions/{session_obj.id}",
            json={"start_time": "14:00", "end_time": "15:00"},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["start_time"] == "14:00"
        assert data["end_time"] == "15:00"

    def test_move_session_to_different_day(self, client, auth_headers_owner, session_obj):
        """Should update session date via PATCH."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = client.patch(
            f"/api/sessions/{session_obj.id}",
            json={"date": tomorrow},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["date"] == tomorrow

    def test_move_session_snaps_time(self, client, auth_headers_owner, session_obj):
        """Moved session times should snap to 5-minute grid."""
        resp = client.patch(
            f"/api/sessions/{session_obj.id}",
            json={"start_time": "14:03"},
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["start_time"] == "14:00"

    def test_cancel_session(self, client, auth_headers_owner, session_obj):
        """Should cancel a session via DELETE."""
        resp = client.delete(
            f"/api/sessions/{session_obj.id}",
            headers=auth_headers_owner,
        )
        assert resp.status_code == 200

        # Verify it's cancelled
        session = db.session.get(Session, session_obj.id)
        assert session.status == "cancelled"


@pytest.mark.integration
class TestScheduleGeneration:
    """Test recurring schedule → session generation."""

    def test_create_schedule_generates_sessions(self, client, auth_headers_owner, class_obj, classroom):
        """Creating a schedule should auto-generate sessions for 12 weeks."""
        resp = client.post(
            f"/api/classes/{class_obj.id}/schedules",
            json={
                "day_of_week": 2,  # Tuesday
                "start_time": "09:00",
                "end_time": "10:00",
                "classroom_id": classroom.id,
            },
            headers=auth_headers_owner,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["sessions_created"] >= 10  # ~12 weeks of Tuesdays

        # Verify sessions exist in the database
        sessions = Session.query.filter_by(
            class_id=class_obj.id,
        ).all()
        assert len(sessions) >= 10
