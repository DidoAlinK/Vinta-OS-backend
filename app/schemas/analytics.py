"""
Analytics schemas — Dashboard stats, Revenue chart, CSV export.
"""
from marshmallow import Schema, fields


class DashboardResponseSchema(Schema):
    """GET /api/analytics/dashboard response."""
    total_students = fields.Integer(metadata={"description": "Total students"})
    total_teachers = fields.Integer(metadata={"description": "Total teachers"})
    total_classes = fields.Integer(metadata={"description": "Total classes"})
    today_sessions = fields.Integer(metadata={"description": "Sessions today"})
    week_sessions = fields.Integer(metadata={"description": "Sessions this week"})
    monthly_income = fields.Integer(metadata={"description": "Monthly income in DA"})
    billing = fields.Dict(metadata={"description": "Billing stats summary"})


class RevenueChartResponseSchema(Schema):
    """GET /api/analytics/revenue-chart response."""
    chart_data = fields.List(fields.Dict, metadata={"description": "Monthly revenue data points"})
