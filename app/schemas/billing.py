"""
Billing schemas — Payment Plans, Student Billing, Payroll, Revenue.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreatePlanRequestSchema(Schema):
    """POST /api/billing/plans"""
    name = fields.String(required=True, metadata={"description": "Plan name", "example": "Monthly — 3,500 DA"})
    duration_days = fields.Integer(required=True, metadata={"description": "Duration in days", "example": 30})
    amount_da = fields.Integer(required=True, metadata={"description": "Amount in DA", "example": 3500})


class RecordPaymentRequestSchema(Schema):
    """POST /api/billing/record-payment"""
    billing_id = fields.String(required=True, metadata={"description": "Student billing record ID", "example": "uuid-string"})
    amount = fields.Integer(required=True, metadata={"description": "Payment amount in DA", "example": 3500})
    payment_method = fields.String(load_default="cash", metadata={"description": "cash / ccp / baridimob / bank_transfer", "example": "cash"})
    notes = fields.String(load_default=None, metadata={"description": "Payment notes"})


# ── Response Schemas ───────────────────────────────────────────────

class PaymentPlanSchema(Schema):
    """Payment plan in list."""
    id = fields.String(metadata={"description": "Plan ID"})
    name = fields.String(metadata={"description": "Plan name"})
    duration_days = fields.Integer(metadata={"description": "Duration in days"})
    amount_da = fields.Integer(metadata={"description": "Amount in DA"})


class PaymentPlanListResponseSchema(Schema):
    """GET /api/billing/plans response."""
    plans = fields.List(fields.Nested(PaymentPlanSchema))


class StudentBillingSchema(Schema):
    """Student billing record."""
    id = fields.String(metadata={"description": "Billing record ID"})
    student_id = fields.String(metadata={"description": "Student ID"})
    student_name = fields.String(metadata={"description": "Student full name"})
    payment_plan_id = fields.String(metadata={"description": "Payment plan ID"})
    amount_da = fields.Integer(metadata={"description": "Billed amount in DA"})
    status = fields.String(metadata={"description": "paid / due / overdue"})
    due_date = fields.String(metadata={"description": "Due date (ISO 8601)"})
    paid_date = fields.String(metadata={"description": "Payment date (ISO 8601)"})
    paid_amount = fields.Integer(metadata={"description": "Amount paid in DA"})
    cycle_start = fields.String(metadata={"description": "Billing cycle start (ISO 8601)"})
    cycle_end = fields.String(metadata={"description": "Billing cycle end (ISO 8601)"})
    days_overdue = fields.Integer(metadata={"description": "Days past due date"})


class StudentBillingListResponseSchema(Schema):
    """GET /api/billing/students response."""
    billings = fields.List(fields.Nested(StudentBillingSchema))


class BillingStatsResponseSchema(Schema):
    """GET /api/billing/stats response."""
    total_due = fields.Integer(metadata={"description": "Total amount due"})
    total_paid = fields.Integer(metadata={"description": "Total amount paid"})
    total_overdue = fields.Integer(metadata={"description": "Total overdue amount"})
    students_paid = fields.Integer(metadata={"description": "Students with paid status"})
    students_due = fields.Integer(metadata={"description": "Students with due status"})
    students_overdue = fields.Integer(metadata={"description": "Students with overdue status"})


class RevenueChartEntrySchema(Schema):
    """Single month in revenue chart."""
    month = fields.String(metadata={"description": "Month label (e.g., 'Sep 2026')"})
    revenue = fields.Integer(metadata={"description": "Revenue in DA"})


class RevenueChartResponseSchema(Schema):
    """GET /api/billing/revenue-chart response."""
    chart_data = fields.List(fields.Nested(RevenueChartEntrySchema))


class AgingBucketsResponseSchema(Schema):
    """GET /api/billing/aging-buckets response."""
    recent_1_7 = fields.List(fields.Dict, metadata={"description": "1-7 days overdue"})
    aging_8_30 = fields.List(fields.Dict, metadata={"description": "8-30 days overdue"})
    critical_30plus = fields.List(fields.Dict, metadata={"description": "30+ days overdue"})


class PayrollSchema(Schema):
    """Payroll record."""
    id = fields.String(metadata={"description": "Payroll record ID"})
    teacher_id = fields.String(metadata={"description": "Teacher ID"})
    teacher_name = fields.String(metadata={"description": "Teacher full name"})
    period_start = fields.String(metadata={"description": "Period start (ISO 8601)"})
    period_end = fields.String(metadata={"description": "Period end (ISO 8601)"})
    total_hours = fields.Float(metadata={"description": "Total hours logged"})
    total_students = fields.Integer(metadata={"description": "Active student count"})
    rate_applied = fields.Integer(metadata={"description": "Rate used for calculation"})
    calculated_amount = fields.Integer(metadata={"description": "Calculated pay in DA"})
    status = fields.String(metadata={"description": "pending / settled / overdue"})
    paid_date = fields.String(metadata={"description": "Payment date (ISO 8601)"})


class PayrollListResponseSchema(Schema):
    """GET /api/billing/payroll response."""
    payrolls = fields.List(fields.Nested(PayrollSchema))


class RecordPaymentResponseSchema(Schema):
    """POST /api/billing/record-payment response."""
    id = fields.String(metadata={"description": "Payment log ID"})
    billing_id = fields.String(metadata={"description": "Billing record ID"})
    amount = fields.Integer(metadata={"description": "Amount paid in DA"})
    payment_method = fields.String(metadata={"description": "Payment method"})
    paid_at = fields.String(metadata={"description": "Payment timestamp (ISO 8601)"})
