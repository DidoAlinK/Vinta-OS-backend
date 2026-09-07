"""
Class schemas — Classes, Classrooms, Schedules.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateClassRequestSchema(Schema):
    """POST /api/classes"""
    name = fields.String(required=True, description="Class name", example="Math — CM2")
    subject = fields.String(load_default=None, description="Primary subject", example="Math")
    color = fields.String(load_default="#b3872a", description="Calendar color hex", example="#b3872a")
    teacher_id = fields.String(load_default=None, description="Assigned teacher ID")
    capacity = fields.Integer(load_default=25, description="Max students", example=25)


class UpdateClassRequestSchema(Schema):
    """PUT /api/classes/<id>"""
    name = fields.String(description="Class name")
    subject = fields.String(description="Primary subject")
    color = fields.String(description="Calendar color hex")
    teacher_id = fields.String(description="Assigned teacher ID")
    capacity = fields.Integer(description="Max students")


class CreateClassroomRequestSchema(Schema):
    """POST /api/classrooms"""
    name = fields.String(required=True, description="Room name", example="Room 101")
    capacity = fields.Integer(load_default=30, description="Max capacity", example=30)


class CreateScheduleRequestSchema(Schema):
    """POST /api/classes/<id>/schedules"""
    day_of_week = fields.Integer(required=True, description="0=Sun, 1=Mon, ..., 6=Sat", example=1)
    start_time = fields.String(required=True, description="Start time (HH:MM)", example="08:00")
    end_time = fields.String(required=True, description="End time (HH:MM)", example="09:00")
    classroom_id = fields.String(load_default=None, description="Classroom ID")


# ── Response Schemas ───────────────────────────────────────────────

class ClassListSchema(Schema):
    """Single class in list."""
    id = fields.String(description="Class ID")
    name = fields.String(description="Class name")
    subject = fields.String(description="Primary subject")
    color = fields.String(description="Calendar color hex")
    teacher_id = fields.String(description="Assigned teacher ID")
    teacher_name = fields.String(description="Teacher full name")
    capacity = fields.Integer(description="Max students")
    enrolled_count = fields.Integer(description="Currently enrolled students")


class ClassListResponseSchema(Schema):
    """GET /api/classes response."""
    classes = fields.List(fields.Nested(ClassListSchema))


class ClassroomSchema(Schema):
    """Classroom in list."""
    id = fields.String(description="Classroom ID")
    name = fields.String(description="Room name")
    capacity = fields.Integer(description="Max capacity")


class ClassroomListResponseSchema(Schema):
    """GET /api/classrooms response."""
    classrooms = fields.List(fields.Nested(ClassroomSchema))


class ScheduleSchema(Schema):
    """Schedule entry."""
    id = fields.String(description="Schedule ID")
    class_id = fields.String(description="Class ID")
    day_of_week = fields.Integer(description="0=Sun, 1=Mon, ..., 6=Sat")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
    classroom_id = fields.String(description="Classroom ID")


class CreateScheduleResponseSchema(Schema):
    """POST /api/classes/<id>/schedules response."""
    id = fields.String(description="Schedule ID")
    day_of_week = fields.Integer(description="Day of week")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
    classroom_id = fields.String(description="Classroom ID")
    sessions_created = fields.Integer(description="Number of sessions generated")


class CreateClassResponseSchema(Schema):
    """POST /api/classes response."""
    id = fields.String(description="Class ID")
    name = fields.String(description="Class name")
    subject = fields.String(description="Subject")
    teacher_id = fields.String(description="Teacher ID")
    capacity = fields.Integer(description="Max students")
