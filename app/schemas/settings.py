"""
Settings schemas — Academy Config, Staff Management, Automations, Profile, Subscription.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class UpdateAcademyRequestSchema(Schema):
    """PUT /api/settings/academy"""
    name = fields.String(metadata={"description": "Academy name"})
    phone = fields.String(metadata={"description": "Phone number"})
    email = fields.String(metadata={"description": "Contact email"})
    address = fields.String(metadata={"description": "Physical address"})
    weekend_day = fields.Integer(metadata={"description": "Weekend day (0=Sun, 5=Fri)"})
    current_term = fields.String(metadata={"description": "Current academic term", "example": "2026 — Fall term"})


class UpdateAppearanceRequestSchema(Schema):
    """PUT /api/settings/appearance"""
    theme = fields.String(metadata={"description": "light or dark", "example": "light"})
    font_size = fields.String(metadata={"description": "small, medium, or large", "example": "medium"})
    language = fields.String(metadata={"description": "Language code: fr, ar, en", "example": "fr"})


class UpdateBillingConfigRequestSchema(Schema):
    """PUT /api/settings/billing-config"""
    currency = fields.String(metadata={"description": "Currency code", "example": "DZD"})
    default_plan_duration = fields.Integer(metadata={"description": "Default plan duration in days", "example": 30})
    billing_reminder_days_before = fields.Integer(metadata={"description": "Reminder days before due", "example": 3})
    due_date_reminder_timing = fields.String(metadata={"description": "Reminder time", "example": "09:00"})
    whatsapp_template = fields.String(metadata={"description": "WhatsApp message template"})


class UpdateAutomationsRequestSchema(Schema):
    """PUT /api/settings/automations"""
    auto_checkout_enabled = fields.Boolean(metadata={"description": "Enable auto-checkout at class end"})
    end_class_popup_enabled = fields.Boolean(metadata={"description": "Enable end-of-class popup"})


class AddStaffRequestSchema(Schema):
    """POST /api/settings/staff"""
    name = fields.String(required=True, metadata={"description": "Staff name", "example": "Fatima Zohra"})
    pin = fields.String(required=True, metadata={"description": "4-6 digit PIN", "example": "5678"})
    phone = fields.String(load_default=None, metadata={"description": "Phone number"})
    role = fields.String(load_default="staff", metadata={"description": "Role: owner or staff"})
    owner_pin = fields.String(required=True, metadata={"description": "Owner's PIN for authorization", "example": "1234"})


class UpdateStaffRequestSchema(Schema):
    """PUT /api/settings/staff/<id>"""
    name = fields.String(metadata={"description": "Staff name"})
    phone = fields.String(metadata={"description": "Phone number"})
    role = fields.String(metadata={"description": "Role: owner or staff"})


class UpdateProfileRequestSchema(Schema):
    """PUT /api/settings/profile"""
    name = fields.String(metadata={"description": "User name"})
    phone = fields.String(metadata={"description": "Phone number"})
    email = fields.String(metadata={"description": "Email address"})


# ── Response Schemas ───────────────────────────────────────────────

class AcademyResponseSchema(Schema):
    """GET /api/settings/academy response."""
    id = fields.String(metadata={"description": "Academy ID"})
    name = fields.String(metadata={"description": "Academy name"})
    phone = fields.String(metadata={"description": "Phone number"})
    email = fields.String(metadata={"description": "Contact email"})
    address = fields.String(metadata={"description": "Physical address"})
    weekend_day = fields.Integer(metadata={"description": "Weekend day (0=Sun, 5=Fri)"})
    current_term = fields.String(metadata={"description": "Current academic term"})


class AppearanceResponseSchema(Schema):
    """GET /api/settings/appearance response."""
    theme = fields.String(metadata={"description": "light or dark"})
    font_size = fields.String(metadata={"description": "small, medium, or large"})
    language = fields.String(metadata={"description": "Language code"})


class BillingConfigResponseSchema(Schema):
    """GET /api/settings/billing-config response."""
    currency = fields.String(metadata={"description": "Currency code"})
    default_plan_duration = fields.Integer(metadata={"description": "Default plan duration in days"})
    billing_reminder_days_before = fields.Integer(metadata={"description": "Reminder days before due"})
    due_date_reminder_timing = fields.String(metadata={"description": "Reminder time"})
    whatsapp_template = fields.String(metadata={"description": "WhatsApp message template"})


class AutomationsResponseSchema(Schema):
    """GET /api/settings/automations response."""
    auto_checkout_enabled = fields.Boolean(metadata={"description": "Auto-checkout enabled"})
    end_class_popup_enabled = fields.Boolean(metadata={"description": "End-class popup enabled"})
    tier = fields.String(metadata={"description": "Current subscription tier"})


class StaffSchema(Schema):
    """Staff member in list."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "Staff name"})
    role = fields.String(metadata={"description": "Role: owner or staff"})
    phone = fields.String(metadata={"description": "Phone number"})
    is_active = fields.Boolean(metadata={"description": "Account active status"})


class StaffListResponseSchema(Schema):
    """GET /api/settings/staff response."""
    staff = fields.List(fields.Nested(StaffSchema))


class AddStaffResponseSchema(Schema):
    """POST /api/settings/staff response."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "Staff name"})
    role = fields.String(metadata={"description": "Role: owner or staff"})


class ProfileResponseSchema(Schema):
    """GET /api/settings/profile response."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "User name"})
    email = fields.String(metadata={"description": "Email address"})
    phone = fields.String(metadata={"description": "Phone number"})
    role = fields.String(metadata={"description": "Role: owner or staff"})
    picture = fields.String(metadata={"description": "Profile picture URL"})


class SubscriptionResponseSchema(Schema):
    """GET /api/settings/subscription response."""
    tier = fields.String(metadata={"description": "Subscription tier: starter, pro, scaler"})
    status = fields.String(metadata={"description": "active, inactive, trial"})
    invoicing_method = fields.String(metadata={"description": "Invoicing method"})
    started_at = fields.String(metadata={"description": "Subscription start (ISO 8601)"})
    expires_at = fields.String(metadata={"description": "Subscription expiry (ISO 8601)"})
