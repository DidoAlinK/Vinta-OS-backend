"""
Calendar schemas — Session CRUD, Week/Day views, Drag-and-drop.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateSessionRequestSchema(Schema):
    """POST /api/sessions"""
    class_id = fields.String(required=True, description="Class ID", example="uuid-string")
    date = fields.String(required=True, description="Session date (ISO 8601)", example="2026-09-07")
    start_time = fields.String(required=True, description="Start time (HH:MM)", example="10:00")
    end_time = fields.String(required=True, description="End time (HH:MM)", example="11:00")
    teacher_id = fields.String(load_default=None, description="Teacher ID (defaults to class teacher)")
    classroom_id = fields.String(load_default=None, description="Classroom ID")
    subject = fields.String(load_default=None, description="Subject (defaults to class subject)")


class UpdateSessionRequestSchema(Schema):
    """PATCH /api/sessions/<id>"""
    date = fields.String(load_default=None, description="New date (ISO 8601)")
    start_time = fields.String(load_default=None, description="New start time (HH:MM)")
    end_time = fields.String(load_default=None, description="New end time (HH:MM)")


# ── Response Schemas ───────────────────────────────────────────────

class SessionSchema(Schema):
    """Single session in calendar view."""
    id = fields.String(description="Session ID")
    class_id = fields.String(description="Class ID")
    class_name = fields.String(description="Class name")
    teacher_id = fields.String(description="Teacher ID")
    teacher_name = fields.String(description="Teacher full name")
    classroom_id = fields.String(description="Classroom ID")
    date = fields.String(description="Session date (ISO 8601)")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
    subject = fields.String(description="Subject")
    status = fields.String(description="scheduled / in_progress / completed / cancelled")
    color = fields.String(description="Calendar color from class")


class WeekSessionsResponseSchema(Schema):
    """GET /api/calendar/week response."""
    week_start = fields.String(description="Week start date (ISO 8601)")
    sessions = fields.List(fields.Nested(SessionSchema))


class DaySessionsResponseSchema(Schema):
    """GET /api/calendar/day response."""
    date = fields.String(description="Requested date (ISO 8601)")
    sessions = fields.List(fields.Nested(SessionSchema))


class CreateSessionResponseSchema(Schema):
    """POST /api/sessions response."""
    id = fields.String(description="Session ID")
    class_id = fields.String(description="Class ID")
    date = fields.String(description="Session date (ISO 8601)")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
    subject = fields.String(description="Subject")
    status = fields.String(description="Session status")


class UpdateSessionResponseSchema(Schema):
    """PATCH /api/sessions/<id> response."""
    id = fields.String(description="Session ID")
    date = fields.String(description="Session date (ISO 8601)")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
