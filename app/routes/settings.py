"""
Vinta School OS — Settings Blueprint
/api/settings — Academy Config, Staff Management, Automations, Profile
"""
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.utils.decorators import tenant_required, owner_only
from app.models.user import User
from app.models.academy import Academy, AcademySettings, Subscription
from app.services import tenant_service, auth_service, export_service

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/academy", methods=["GET"])
@jwt_required()
@tenant_required
def get_academy():
    """Get academy profile details."""
    from flask import g
    academy = g.current_academy
    return jsonify({
        "id": academy.id,
        "name": academy.name,
        "phone": academy.phone,
        "email": academy.email,
        "address": academy.address,
        "weekend_day": academy.weekend_day,
        "current_term": academy.current_term,
    }), 200


@settings_bp.route("/academy", methods=["PUT"])
@jwt_required()
@tenant_required
@owner_only
def update_academy():
    """
    Update academy profile (owner-only).
    Body: { name?, phone?, email?, address?, weekend_day?, current_term? }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    academy = g.current_academy
    for field in ("name", "phone", "email", "address", "weekend_day", "current_term"):
        if field in data:
            setattr(academy, field, data[field])

    db.session.commit()
    return jsonify({"message": "Academy updated"}), 200


@settings_bp.route("/appearance", methods=["GET"])
@jwt_required()
@tenant_required
def get_appearance():
    """Get appearance settings."""
    from flask import g
    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    if not settings:
        return jsonify({"error": "Settings not found"}), 404

    return jsonify({
        "theme": settings.default_theme,
        "font_size": settings.default_font_size,
        "language": settings.default_language,
    }), 200


@settings_bp.route("/appearance", methods=["PUT"])
@jwt_required()
@tenant_required
def update_appearance():
    """
    Update appearance settings.
    Body: { theme?, font_size?, language? }
    """
    from flask import g
    data = request.get_json()
    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    if not settings:
        return jsonify({"error": "Settings not found"}), 404

    if "theme" in data:
        settings.default_theme = data["theme"]
    if "font_size" in data:
        settings.default_font_size = data["font_size"]
    if "language" in data:
        settings.default_language = data["language"]

    db.session.commit()
    return jsonify({"message": "Appearance updated"}), 200


@settings_bp.route("/billing-config", methods=["GET"])
@jwt_required()
@tenant_required
@owner_only
def get_billing_config():
    """Get billing configuration (owner-only)."""
    from flask import g
    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    if not settings:
        return jsonify({"error": "Settings not found"}), 404

    return jsonify({
        "currency": settings.currency,
        "default_plan_duration": settings.default_plan_duration,
        "billing_reminder_days_before": settings.billing_reminder_days_before,
        "due_date_reminder_timing": settings.due_date_reminder_timing,
        "whatsapp_template": settings.whatsapp_template,
    }), 200


@settings_bp.route("/billing-config", methods=["PUT"])
@jwt_required()
@tenant_required
@owner_only
def update_billing_config():
    """
    Update billing configuration (owner-only).
    Body: { currency?, default_plan_duration?, billing_reminder_days_before?,
            due_date_reminder_timing?, whatsapp_template? }
    """
    from flask import g
    data = request.get_json()
    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    if not settings:
        return jsonify({"error": "Settings not found"}), 404

    for field in ("currency", "default_plan_duration", "billing_reminder_days_before",
                  "due_date_reminder_timing", "whatsapp_template"):
        if field in data:
            setattr(settings, field, data[field])

    db.session.commit()
    return jsonify({"message": "Billing config updated"}), 200


@settings_bp.route("/automations", methods=["GET"])
@jwt_required()
@tenant_required
@owner_only
def get_automations():
    """Get automation settings (owner-only, gated by Scaler tier)."""
    from flask import g
    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    subscription = Subscription.query.filter_by(academy_id=g.current_academy_id).first()

    return jsonify({
        "auto_checkout_enabled": settings.auto_checkout_enabled if settings else True,
        "end_class_popup_enabled": settings.end_class_popup_enabled if settings else True,
        "tier": subscription.tier if subscription else "starter",
    }), 200


@settings_bp.route("/automations", methods=["PUT"])
@jwt_required()
@tenant_required
@owner_only
def update_automations():
    """
    Update automation settings (owner-only).
    Body: { auto_checkout_enabled?, end_class_popup_enabled? }
    Gated by Scaler subscription tier.
    """
    from flask import g
    data = request.get_json()

    subscription = Subscription.query.filter_by(academy_id=g.current_academy_id).first()
    if subscription and subscription.tier not in ("pro", "scaler"):
        return jsonify({"error": "Automations require Pro or Scaler tier"}), 403

    settings = AcademySettings.query.filter_by(academy_id=g.current_academy_id).first()
    if not settings:
        return jsonify({"error": "Settings not found"}), 404

    if "auto_checkout_enabled" in data:
        settings.auto_checkout_enabled = data["auto_checkout_enabled"]
    if "end_class_popup_enabled" in data:
        settings.end_class_popup_enabled = data["end_class_popup_enabled"]

    db.session.commit()
    return jsonify({"message": "Automations updated"}), 200


# ── Staff Management ────────────────────────────────────────────────

@settings_bp.route("/staff", methods=["GET"])
@jwt_required()
@tenant_required
@owner_only
def list_staff():
    """List all staff profiles for the academy (owner-only)."""
    from flask import g
    profiles = tenant_service.get_academy_profiles(g.current_academy_id)
    return jsonify({
        "staff": [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "phone": p.phone,
                "is_active": p.is_active,
            }
            for p in profiles
        ]
    }), 200


@settings_bp.route("/staff", methods=["POST"])
@jwt_required()
@tenant_required
@owner_only
def add_staff():
    """
    Add a new staff profile (owner-only, requires owner PIN).
    Body: { name, pin, phone?, role? }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Verify owner PIN
    owner_pin = data.get("owner_pin")
    if not owner_pin or not g.current_user.verify_pin(owner_pin):
        return jsonify({"error": "Owner PIN verification required"}), 401

    required = ("name", "pin")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    user = tenant_service.create_staff_profile(
        academy_id=g.current_academy_id,
        name=data["name"],
        pin=data["pin"],
        phone=data.get("phone"),
        role=data.get("role", "staff"),
    )
    db.session.commit()

    return jsonify({
        "id": user.id,
        "name": user.name,
        "role": user.role,
    }), 201


@settings_bp.route("/staff/<user_id>", methods=["PUT"])
@jwt_required()
@tenant_required
@owner_only
def update_staff(user_id):
    """Update a staff profile."""
    user = db.session.get(User, user_id)
    if not user or user.academy_id != g.current_academy_id:
        return jsonify({"error": "Staff not found"}), 404

    data = request.get_json()
    for field in ("name", "phone", "role"):
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({"message": "Staff updated"}), 200


@settings_bp.route("/staff/<user_id>/deactivate", methods=["POST"])
@jwt_required()
@tenant_required
@owner_only
def deactivate_staff(user_id):
    """Deactivate a staff profile (soft-delete)."""
    user = db.session.get(User, user_id)
    if not user or user.academy_id != g.current_academy_id:
        return jsonify({"error": "Staff not found"}), 404

    if user.role == "owner":
        return jsonify({"error": "Cannot deactivate an owner account"}), 400

    user.is_active = False
    db.session.commit()
    return jsonify({"message": "Staff deactivated"}), 200


# ── Profile ─────────────────────────────────────────────────────────

@settings_bp.route("/profile", methods=["GET"])
@jwt_required()
@tenant_required
def get_profile():
    """Get current user's profile."""
    from flask import g
    user = g.current_user
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "picture": user.picture,
    }), 200


@settings_bp.route("/profile", methods=["PUT"])
@jwt_required()
@tenant_required
def update_profile():
    """
    Update current user's profile.
    Body: { name?, phone?, email? }
    """
    from flask import g
    data = request.get_json()
    user = g.current_user

    for field in ("name", "phone", "email"):
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


# ── Subscription ────────────────────────────────────────────────────

@settings_bp.route("/subscription", methods=["GET"])
@jwt_required()
@tenant_required
@owner_only
def get_subscription():
    """Get academy subscription details (owner-only)."""
    from flask import g
    sub = Subscription.query.filter_by(academy_id=g.current_academy_id).first()
    if not sub:
        return jsonify({"error": "Subscription not found"}), 404

    return jsonify({
        "tier": sub.tier,
        "status": sub.status,
        "invoicing_method": sub.invoicing_method,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }), 200
