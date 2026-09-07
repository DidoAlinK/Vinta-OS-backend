"""
Teacher schemas — CRUD, Contracts, Payroll.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateTeacherRequestSchema(Schema):
    """POST /api/teachers"""
    first_name = fields.String(required=True, description="First name", example="Ali")
    last_name = fields.String(required=True, description="Last name", example="Bensalem")
    phone = fields.String(load_default=None, description="Phone number", example="+213555987654")
    subject = fields.String(load_default=None, description="Primary subject", example="Math")
    notes = fields.String(load_default=None, description="Free-form notes")
    contract_type = fields.String(load_default="hourly", description="hourly or per_student", example="hourly")
    hourly_rate = fields.Integer(load_default=0, description="DA per hour", example=1500)
    per_student_rate = fields.Integer(load_default=0, description="DA per student", example=500)


class UpdateTeacherRequestSchema(Schema):
    """PUT /api/teachers/<id>"""
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    phone = fields.String(description="Phone number")
    subject = fields.String(description="Primary subject")
    notes = fields.String(description="Notes")
    contract_type = fields.String(description="hourly or per_student")
    hourly_rate = fields.Integer(description="DA per hour")
    per_student_rate = fields.Integer(description="DA per student")


# ── Response Schemas ───────────────────────────────────────────────

class TeacherListSchema(Schema):
    """Single teacher in list."""
    id = fields.String(description="Teacher ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    full_name = fields.String(description="Computed full name")
    phone = fields.String(description="Phone number")
    subject = fields.String(description="Primary subject")
    contract_type = fields.String(description="hourly or per_student")
    hourly_rate = fields.Integer(description="DA per hour")
    per_student_rate = fields.Integer(description="DA per student")
    classes_assigned = fields.List(fields.String, description="Assigned class names")
    sessions_this_week = fields.Integer(description="Sessions scheduled this week")
    created_at = fields.String(description="Created at (ISO 8601)")


class TeacherListResponseSchema(Schema):
    """GET /api/teachers response."""
    teachers = fields.List(fields.Nested(TeacherListSchema))


class TeacherStatsResponseSchema(Schema):
    """GET /api/teachers/stats response."""
    total = fields.Integer(description="Total teachers")
    hourly = fields.Integer(description="Hourly contract count")
    per_student = fields.Integer(description="Per-student contract count")


class ScheduleEntrySchema(Schema):
    """Single schedule entry in teacher profile."""
    id = fields.String(description="Session ID")
    class_name = fields.String(description="Class name")
    date = fields.String(description="Session date (ISO 8601)")
    start_time = fields.String(description="Start time (HH:MM)")
    end_time = fields.String(description="End time (HH:MM)")
    subject = fields.String(description="Subject")


class PayrollSummarySchema(Schema):
    """Payroll summary in teacher profile."""
    teacher_id = fields.String(description="Teacher ID")
    contract_type = fields.String(description="Contract type")
    hourly_rate = fields.Integer(description="DA per hour")
    per_student_rate = fields.Integer(description="DA per student")
    current_payroll = fields.Dict(description="Current month payroll info")
    hours_this_week = fields.Float(description="Hours logged this week")
    active_students = fields.Integer(description="Active students (per-student contracts)")


class TeacherProfileResponseSchema(Schema):
    """GET /api/teachers/<id> — full teacher profile."""
    id = fields.String(description="Teacher ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    full_name = fields.String(description="Computed full name")
    phone = fields.String(description="Phone number")
    subject = fields.String(description="Primary subject")
    notes = fields.String(description="Notes")
    contract_type = fields.String(description="hourly or per_student")
    hourly_rate = fields.Integer(description="DA per hour")
    per_student_rate = fields.Integer(description="DA per student")
    classes_assigned = fields.List(fields.String, description="Assigned class names")
    schedule = fields.List(fields.Nested(ScheduleEntrySchema))
    payroll_summary = fields.Nested(PayrollSummarySchema)


class CreateTeacherResponseSchema(Schema):
    """POST /api/teachers response."""
    id = fields.String(description="Teacher ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
