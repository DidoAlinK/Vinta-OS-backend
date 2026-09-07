"""
Attendance schemas — Check-in/out, Roster, Auto-checkout.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CheckInRequestSchema(Schema):
    """POST /api/attendance/check-in"""
    session_id = fields.String(required=True, description="Session ID", example="uuid-string")
    student_id = fields.String(required=True, description="Student ID", example="uuid-string")
    pin = fields.String(required=True, description="Staff PIN for attribution", example="1234")


class CheckOutRequestSchema(Schema):
    """POST /api/attendance/check-out"""
    session_id = fields.String(required=True, description="Session ID", example="uuid-string")
    student_id = fields.String(required=True, description="Student ID", example="uuid-string")


class AutoCheckoutRequestSchema(Schema):
    """POST /api/attendance/auto-checkout"""
    session_id = fields.String(required=True, description="Session ID", example="uuid-string")


class AddToSessionRequestSchema(Schema):
    """POST /api/attendance/add-to-session"""
    session_id = fields.String(required=True, description="Session ID", example="uuid-string")
    student_id = fields.String(required=True, description="Student ID", example="uuid-string")


# ── Response Schemas ───────────────────────────────────────────────

class CheckInResponseSchema(Schema):
    """POST /api/attendance/check-in response."""
    id = fields.String(description="SessionStudent record ID")
    student_id = fields.String(description="Student ID")
    is_present = fields.Boolean(description="Attendance status")
    checked_in_at = fields.String(description="Check-in timestamp (ISO 8601)")
    checked_in_by = fields.String(description="User ID who performed check-in")


class CheckOutResponseSchema(Schema):
    """POST /api/attendance/check-out response."""
    id = fields.String(description="SessionStudent record ID")
    student_id = fields.String(description="Student ID")
    checked_out_at = fields.String(description="Check-out timestamp (ISO 8601)")


class AutoCheckoutResponseSchema(Schema):
    """POST /api/attendance/auto-checkout response."""
    session_id = fields.String(description="Session ID")
    checked_out_count = fields.Integer(description="Number of students checked out")


class RosterEntrySchema(Schema):
    """Single entry in the session roster."""
    id = fields.String(description="SessionStudent record ID")
    student_id = fields.String(description="Student ID")
    student_name = fields.String(description="Student full name")
    is_present = fields.Boolean(description="Attendance status")
    checked_in_at = fields.String(description="Check-in timestamp (ISO 8601)")
    checked_out_at = fields.String(description="Check-out timestamp (ISO 8601)")
    checked_in_by = fields.String(description="User ID who performed check-in")
    payment_status = fields.String(description="paid / unpaid / partial")


class RosterResponseSchema(Schema):
    """GET /api/attendance/roster/<session_id> response."""
    roster = fields.List(fields.Nested(RosterEntrySchema))


class AddToSessionResponseSchema(Schema):
    """POST /api/attendance/add-to-session response."""
    id = fields.String(description="SessionStudent record ID")
    student_id = fields.String(description="Student ID")
    is_present = fields.Boolean(description="Attendance status")
