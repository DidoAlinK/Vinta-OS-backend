"""
Student schemas — CRUD, Guardians, Enrollments, Profile Drawer.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateStudentRequestSchema(Schema):
    """POST /api/students"""
    first_name = fields.String(required=True, description="First name", example="Yasmine")
    last_name = fields.String(required=True, description="Last name", example="Benali")
    phone = fields.String(load_default=None, description="Student phone", example="+213555111222")
    parent_phone = fields.String(load_default=None, description="Parent phone", example="+213555333444")
    notes = fields.String(load_default=None, description="Free-form notes")


class UpdateStudentRequestSchema(Schema):
    """PUT /api/students/<id>"""
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    phone = fields.String(description="Student phone")
    parent_phone = fields.String(description="Parent phone")
    notes = fields.String(description="Free-form notes")


class EnrollStudentRequestSchema(Schema):
    """POST /api/students/<id>/enroll"""
    class_id = fields.String(required=True, description="Class ID to enroll in", example="uuid-string")


class AddGuardianRequestSchema(Schema):
    """POST /api/students/<id>/guardians"""
    name = fields.String(required=True, description="Guardian name", example="Mr. Benali")
    relationship = fields.String(load_default=None, description="Relationship type", example="Father")
    phone = fields.String(required=True, description="Guardian phone", example="+213555333444")
    is_emergency = fields.Boolean(load_default=False, description="Emergency contact flag")


# ── Response Schemas ───────────────────────────────────────────────

class StudentListSchema(Schema):
    """Single student in list."""
    id = fields.String(description="Student ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    full_name = fields.String(description="Computed full name")
    phone = fields.String(description="Phone number")
    parent_phone = fields.String(description="Parent phone")
    enrollment_status = fields.String(description="active / inactive / withdrawn")
    billing_status = fields.String(description="paid / due / overdue")
    days_until_due = fields.Integer(description="Days until next payment is due")


class StudentListResponseSchema(Schema):
    """GET /api/students response."""
    students = fields.List(fields.Nested(StudentListSchema))
    total = fields.Integer(description="Total student count")
    page = fields.Integer(description="Current page")
    per_page = fields.Integer(description="Page size")


class StudentStatsResponseSchema(Schema):
    """GET /api/students/stats response."""
    total = fields.Integer(description="Total students")
    active = fields.Integer(description="Active students")
    inactive = fields.Integer(description="Inactive students")
    new_this_month = fields.Integer(description="New students this month")


class GuardianSchema(Schema):
    """Guardian in student profile."""
    id = fields.String(description="Guardian ID")
    name = fields.String(description="Guardian name")
    relationship = fields.String(description="Relationship type")
    phone = fields.String(description="Phone number")
    is_emergency = fields.Boolean(description="Emergency contact")


class EnrollmentSchema(Schema):
    """Enrollment in student profile."""
    id = fields.String(description="Enrollment ID")
    class_id = fields.String(description="Class ID")
    class_name = fields.String(description="Class name")
    status = fields.String(description="active / withdrawn")


class StudentProfileResponseSchema(Schema):
    """GET /api/students/<id> — full profile drawer."""
    id = fields.String(description="Student ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    full_name = fields.String(description="Computed full name")
    phone = fields.String(description="Phone number")
    parent_phone = fields.String(description="Parent phone")
    notes = fields.String(description="Notes")
    created_at = fields.String(description="Created at (ISO 8601)")
    guardians = fields.List(fields.Nested(GuardianSchema))
    enrollments = fields.List(fields.Nested(EnrollmentSchema))
    billing = fields.Dict(description="Current billing info")


class CreateStudentResponseSchema(Schema):
    """POST /api/students response."""
    id = fields.String(description="Student ID")
    first_name = fields.String(description="First name")
    last_name = fields.String(description="Last name")
    full_name = fields.String(description="Computed full name")


class EnrollResponseSchema(Schema):
    """POST /api/students/<id>/enroll response."""
    id = fields.String(description="Enrollment ID")
    student_id = fields.String(description="Student ID")
    class_id = fields.String(description="Class ID")
    status = fields.String(description="Enrollment status")
