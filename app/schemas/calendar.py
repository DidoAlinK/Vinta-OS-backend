"""
Calendar schemas — Session CRUD, Week/Day views, Drag-and-drop.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateSessionRequestSchema(Schema):
    """POST /api/sessions"""
    class_id = fields.String(required=True, metadata={"description": "Class ID", "example": "uuid-string"})
    date = fields.String(required=True, metadata={"description": "Session date (ISO 8601)", "example": "2026-09-07"})
    start_time = fields.String(required=True, metadata={"description": "Start time (HH:MM)", "example": "10:00"})
    end_time = fields.String(required=True, metadata={"description": "End time (HH:MM)", "example": "11:00"})
    teacher_id = fields.String(load_default=None, metadata={"description": "Teacher ID (defaults to class teacher)"})
    classroom_id = fields.String(load_default=None, metadata={"description": "Classroom ID"})
    subject = fields.String(load_default=None, metadata={"description": "Subject (defaults to class subject)"})


class UpdateSessionRequestSchema(Schema):
    """PATCH /api/sessions/<id>"""
    date = fields.String(load_default=None, metadata={"description": "New date (ISO 8601)"})
    start_time = fields.String(load_default=None, metadata={"description": "New start time (HH:MM)"})
    end_time = fields.String(load_default=None, metadata={"description": "New end time (HH:MM)"})


# ── Response Schemas ───────────────────────────────────────────────

class SessionSchema(Schema):
    """Single session in calendar view."""
    id = fields.String(metadata={"description": "Session ID"})
    class_id = fields.String(metadata={"description": "Class ID"})
    class_name = fields.String(metadata={"description": "Class name"})
    teacher_id = fields.String(metadata={"description": "Teacher ID"})
    teacher_name = fields.String(metadata={"description": "Teacher full name"})
    classroom_id = fields.String(metadata={"description": "Classroom ID"})
    date = fields.String(metadata={"description": "Session date (ISO 8601)"})
    start_time = fields.String(metadata={"description": "Start time (HH:MM)"})
    end_time = fields.String(metadata={"description": "End time (HH:MM)"})
    subject = fields.String(metadata={"description": "Subject"})
    status = fields.String(metadata={"description": "scheduled / in_progress / completed / cancelled"})
    color = fields.String(metadata={"description": "Calendar color from class"})


class WeekSessionsResponseSchema(Schema):
    """GET /api/calendar/week response."""
    week_start = fields.String(metadata={"description": "Week start date (ISO 8601)"})
    sessions = fields.List(fields.Nested(SessionSchema))


class DaySessionsResponseSchema(Schema):
    """GET /api/calendar/day response."""
    date = fields.String(metadata={"description": "Requested date (ISO 8601)"})
    sessions = fields.List(fields.Nested(SessionSchema))


class CreateSessionResponseSchema(Schema):
    """POST /api/sessions response."""
    id = fields.String(metadata={"description": "Session ID"})
    class_id = fields.String(metadata={"description": "Class ID"})
    date = fields.String(metadata={"description": "Session date (ISO 8601)"})
    start_time = fields.String(metadata={"description": "Start time (HH:MM)"})
    end_time = fields.String(metadata={"description": "End time (HH:MM)"})
    subject = fields.String(metadata={"description": "Subject"})
    status = fields.String(metadata={"description": "Session status"})


class UpdateSessionResponseSchema(Schema):
    """PATCH /api/sessions/<id> response."""
    id = fields.String(metadata={"description": "Session ID"})
    date = fields.String(metadata={"description": "Session date (ISO 8601)"})
    start_time = fields.String(metadata={"description": "Start time (HH:MM)"})
    end_time = fields.String(metadata={"description": "End time (HH:MM)"})
