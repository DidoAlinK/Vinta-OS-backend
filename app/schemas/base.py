"""
Base schemas shared across all modules.
"""
from marshmallow import Schema, fields


class ErrorSchema(Schema):
    """Standard error response."""
    error = fields.String(required=True, metadata={"description": "Error message"})


class MessageSchema(Schema):
    """Standard success message response."""
    message = fields.String(required=True, metadata={"description": "Success message"})
