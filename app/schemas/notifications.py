"""
Notification schemas — Toast alerts, Broadcasts.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class CreateNotificationRequestSchema(Schema):
    """POST /api/notifications"""
    type = fields.String(required=True, metadata={"description": "Notification type: info, warning, success, error", "example": "info"})
    title = fields.String(required=True, metadata={"description": "Notification title", "example": "New enrollment"})
    message = fields.String(required=True, metadata={"description": "Notification message", "example": "Yasmine Benali enrolled in Math CM2"})
    detail = fields.String(load_default=None, metadata={"description": "Detailed message"})
    user_id = fields.String(load_default=None, metadata={"description": "Target user ID (null = broadcast)"})
    actions = fields.Dict(load_default=None, metadata={"description": "Action buttons config"})


# ── Response Schemas ───────────────────────────────────────────────

class NotificationSchema(Schema):
    """Single notification."""
    id = fields.String(metadata={"description": "Notification ID"})
    type = fields.String(metadata={"description": "info, warning, success, error"})
    title = fields.String(metadata={"description": "Notification title"})
    message = fields.String(metadata={"description": "Notification message"})
    detail = fields.String(metadata={"description": "Detailed message"})
    actions = fields.Dict(metadata={"description": "Action buttons config"})
    is_read = fields.Boolean(metadata={"description": "Read status"})
    created_at = fields.String(metadata={"description": "Created at (ISO 8601)"})


class NotificationListResponseSchema(Schema):
    """GET /api/notifications response."""
    notifications = fields.List(fields.Nested(NotificationSchema))


class UnreadCountResponseSchema(Schema):
    """GET /api/notifications/unread-count response."""
    unread_count = fields.Integer(metadata={"description": "Number of unread notifications"})


class CreateNotificationResponseSchema(Schema):
    """POST /api/notifications response."""
    id = fields.String(metadata={"description": "Notification ID"})
    type = fields.String(metadata={"description": "Notification type"})
    title = fields.String(metadata={"description": "Notification title"})
