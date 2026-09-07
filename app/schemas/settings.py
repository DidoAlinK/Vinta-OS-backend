"""
Settings schemas — Academy Config, Staff Management, Automations, Profile, Subscription.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class UpdateAcademyRequestSchema(Schema):
    """PUT /api/settings/academy"""
    name = fields.String(description="Academy name")
    phone = fields.String(description="Phone number")
    email = fields.String(description="Contact email")
    address = fields.String(description="Physical address")
    weekend_day = fields.Integer(description="Weekend day (0=Sun, 5=Fri)")
    current_term = fields.String(description="Current academic term", example="2026 — Fall term")


class UpdateAppearanceRequestSchema(Schema):
    """PUT /api/settings/appearance"""
    theme = fields.String(description="light or dark", example="light")
    font_size = fields.String(description="small, medium, or large", example="medium")
    language = fields.String(description="Language code: fr, ar, en", example="fr")


class UpdateBillingConfigRequestSchema(Schema):
    """PUT /api/settings/billing-config"""
    currency = fields.String(description="Currency code", example="DZD")
    default_plan_duration = fields.Integer(description="Default plan duration in days", example=30)
    billing_reminder_days_before = fields.Integer(description="Reminder days before due", example=3)
    due_date_reminder_timing = fields.String(description="Reminder time", example="09:00")
    whatsapp_template = fields.String(description="WhatsApp message template")


class UpdateAutomationsRequestSchema(Schema):
    """PUT /api/settings/automations"""
    auto_checkout_enabled = fields.Boolean(description="Enable auto-checkout at class end")
    end_class_popup_enabled = fields.Boolean(description="Enable end-of-class popup")


class AddStaffRequestSchema(Schema):
    """POST /api/settings/staff"""
    name = fields.String(required=True, description="Staff name", example="Fatima Zohra")
    pin = fields.String(required=True, description="4-6 digit PIN", example="5678")
    phone = fields.String(load_default=None, description="Phone number")
    role = fields.String(load_default="staff", description="Role: owner or staff")
    owner_pin = fields.String(required=True, description="Owner's PIN for authorization", example="1234")


class UpdateStaffRequestSchema(Schema):
    """PUT /api/settings/staff/<id>"""
    name = fields.String(description="Staff name")
    phone = fields.String(description="Phone number")
    role = fields.String(description="Role: owner or staff")


class UpdateProfileRequestSchema(Schema):
    """PUT /api/settings/profile"""
    name = fields.String(description="User name")
    phone = fields.String(description="Phone number")
    email = fields.String(description="Email address")


# ── Response Schemas ───────────────────────────────────────────────

class AcademyResponseSchema(Schema):
    """GET /api/settings/academy response."""
    id = fields.String(description="Academy ID")
    name = fields.String(description="Academy name")
    phone = fields.String(description="Phone number")
    email = fields.String(description="Contact email")
    address = fields.String(description="Physical address")
    weekend_day = fields.Integer(description="Weekend day (0=Sun, 5=Fri)")
    current_term = fields.String(description="Current academic term")


class AppearanceResponseSchema(Schema):
    """GET /api/settings/appearance response."""
    theme = fields.String(description="light or dark")
    font_size = fields.String(description="small, medium, or large")
    language = fields.String(description="Language code")


class BillingConfigResponseSchema(Schema):
    """GET /api/settings/billing-config response."""
    currency = fields.String(description="Currency code")
    default_plan_duration = fields.Integer(description="Default plan duration in days")
    billing_reminder_days_before = fields.Integer(description="Reminder days before due")
    due_date_reminder_timing = fields.String(description="Reminder time")
    whatsapp_template = fields.String(description="WhatsApp message template")


class AutomationsResponseSchema(Schema):
    """GET /api/settings/automations response."""
    auto_checkout_enabled = fields.Boolean(description="Auto-checkout enabled")
    end_class_popup_enabled = fields.Boolean(description="End-class popup enabled")
    tier = fields.String(description="Current subscription tier")


class StaffSchema(Schema):
    """Staff member in list."""
    id = fields.String(description="User ID")
    name = fields.String(description="Staff name")
    role = fields.String(description="Role: owner or staff")
    phone = fields.String(description="Phone number")
    is_active = fields.Boolean(description="Account active status")


class StaffListResponseSchema(Schema):
    """GET /api/settings/staff response."""
    staff = fields.List(fields.Nested(StaffSchema))


class AddStaffResponseSchema(Schema):
    """POST /api/settings/staff response."""
    id = fields.String(description="User ID")
    name = fields.String(description="Staff name")
    role = fields.String(description="Role: owner or staff")


class ProfileResponseSchema(Schema):
    """GET /api/settings/profile response."""
    id = fields.String(description="User ID")
    name = fields.String(description="User name")
    email = fields.String(description="Email address")
    phone = fields.String(description="Phone number")
    role = fields.String(description="Role: owner or staff")
    picture = fields.String(description="Profile picture URL")


class SubscriptionResponseSchema(Schema):
    """GET /api/settings/subscription response."""
    tier = fields.String(description="Subscription tier: starter, pro, scaler")
    status = fields.String(description="active, inactive, trial")
    invoicing_method = fields.String(description="Invoicing method")
    started_at = fields.String(description="Subscription start (ISO 8601)")
    expires_at = fields.String(description="Subscription expiry (ISO 8601)")
