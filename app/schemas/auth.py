"""
Auth schemas — Login, Signup, PIN verification, Profile management.
"""
from marshmallow import Schema, fields


# ── Request Schemas ────────────────────────────────────────────────

class SignupRequestSchema(Schema):
    """POST /api/auth/signup"""
    name = fields.String(required=True, metadata={"description": "Academy name", "example": "Al-Baraka Academy"})
    email = fields.String(required=True, metadata={"description": "Academy email", "example": "admin@albaraka.dz"})
    password = fields.String(required=True, metadata={"description": "Owner password", "example": "SecurePass123!"})


class LoginRequestSchema(Schema):
    """POST /api/auth/login"""
    email = fields.String(required=True, metadata={"description": "Owner email", "example": "owner@albaraka.dz"})
    password = fields.String(required=True, metadata={"description": "Owner password", "example": "SecurePass123!"})


class VerifyPinRequestSchema(Schema):
    """POST /api/auth/verify-pin"""
    user_id = fields.String(required=True, metadata={"description": "Profile user ID", "example": "uuid-string"})
    pin = fields.String(required=True, metadata={"description": "4-6 digit PIN", "example": "1234"})


class CreateOwnerRequestSchema(Schema):
    """POST /api/auth/create-owner"""
    academy_id = fields.String(required=True, metadata={"description": "Academy ID from signup", "example": "uuid-string"})
    name = fields.String(required=True, metadata={"description": "Owner full name", "example": "Ahmed Benali"})
    email = fields.String(required=True, metadata={"description": "Owner email", "example": "ahmed@albaraka.dz"})
    password = fields.String(required=True, metadata={"description": "Owner password", "example": "SecurePass123!"})
    pin = fields.String(required=True, metadata={"description": "4-6 digit PIN for quick login", "example": "1234"})


class CreateProfileRequestSchema(Schema):
    """POST /api/auth/create-profile"""
    name = fields.String(required=True, metadata={"description": "Staff name", "example": "Fatima Zohra"})
    pin = fields.String(required=True, metadata={"description": "4-6 digit PIN", "example": "5678"})
    role = fields.String(load_default="staff", metadata={"description": "Role: owner or staff", "example": "staff"})
    phone = fields.String(load_default=None, metadata={"description": "Phone number", "example": "+213555123456"})
    owner_pin = fields.String(required=True, metadata={"description": "Owner's PIN for authorization", "example": "1234"})


class ChangePinRequestSchema(Schema):
    """POST /api/auth/change-pin"""
    old_pin = fields.String(required=True, metadata={"description": "Current PIN", "example": "1234"})
    new_pin = fields.String(required=True, metadata={"description": "New PIN", "example": "5678"})


# ── Response Schemas ───────────────────────────────────────────────

class TokenResponseSchema(Schema):
    """JWT token response."""
    access_token = fields.String(metadata={"description": "JWT access token"})
    refresh_token = fields.String(metadata={"description": "JWT refresh token (login only)"})
    user_id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "User name"})
    role = fields.String(metadata={"description": "User role: owner or staff"})
    academy_id = fields.String(metadata={"description": "Academy ID"})


class SignupResponseSchema(Schema):
    """POST /api/auth/signup response."""
    academy_id = fields.String(metadata={"description": "Newly created academy ID"})
    name = fields.String(metadata={"description": "Academy name"})


class CreateOwnerResponseSchema(Schema):
    """POST /api/auth/create-owner response."""
    id = fields.String(metadata={"description": "Owner user ID"})
    name = fields.String(metadata={"description": "Owner name"})
    role = fields.String(metadata={"description": "Role: owner"})
    academy_id = fields.String(metadata={"description": "Academy ID"})


class ProfileResponseSchema(Schema):
    """POST /api/auth/create-profile response."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "User name"})
    role = fields.String(metadata={"description": "Role: owner or staff"})


class ProfileListSchema(Schema):
    """Single profile in the profiles list."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "User name"})
    role = fields.String(metadata={"description": "Role: owner or staff"})
    picture = fields.String(metadata={"description": "Profile picture URL"})
    avatar_color_1 = fields.String(metadata={"description": "Avatar gradient color 1"})
    avatar_color_2 = fields.String(metadata={"description": "Avatar gradient color 2"})


class ProfileListResponseSchema(Schema):
    """GET /api/auth/profiles response."""
    profiles = fields.List(fields.Nested(ProfileListSchema))


class MeResponseSchema(Schema):
    """GET /api/auth/me response."""
    id = fields.String(metadata={"description": "User ID"})
    name = fields.String(metadata={"description": "User name"})
    email = fields.String(metadata={"description": "User email"})
    phone = fields.String(metadata={"description": "Phone number"})
    role = fields.String(metadata={"description": "Role: owner or staff"})
    academy_id = fields.String(metadata={"description": "Academy ID"})
    picture = fields.String(metadata={"description": "Profile picture URL"})
    is_active = fields.Boolean(metadata={"description": "Account active status"})
