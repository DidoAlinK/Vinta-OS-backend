"""
Analytics schemas — Dashboard stats, Revenue chart, CSV export.
"""
from marshmallow import Schema, fields


class DashboardResponseSchema(Schema):
    """GET /api/analytics/dashboard response."""
    total_students = fields.Integer(description="Total students")
    total_teachers = fields.Integer(description="Total teachers")
    total_classes = fields.Integer(description="Total classes")
    today_sessions = fields.Integer(description="Sessions today")
    week_sessions = fields.Integer(description="Sessions this week")
    monthly_income = fields.Integer(description="Monthly income in DA")
    billing = fields.Dict(description="Billing stats summary")


class RevenueChartResponseSchema(Schema):
    """GET /api/analytics/revenue-chart response."""
    chart_data = fields.List(fields.Dict, description="Monthly revenue data points")
