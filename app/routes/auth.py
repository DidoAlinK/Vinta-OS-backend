"""
Vinta School OS — Auth Blueprint
/api/auth — Login, Profile Selection, PIN Verification, Academy Signup
"""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.services import auth_service, tenant_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new academy (tenant provisioning).
    Body: { name, email, password }
    Returns: { academy_id, name }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("name", "email", "password")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        result = tenant_service.create_academy(
            name=data["name"],
            email=data["email"],
            password=data["password"],
        )
        db.session.commit()
        return jsonify(result), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Owner login with email + password.
    Body: { email, password }
    Returns: { access_token, refresh_token, user_id, name, role, academy_id }
    """
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required"}), 400

    result = auth_service.authenticate_owner(data["email"], data["password"])
    if not result:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify(result), 200


@auth_bp.route("/profiles", methods=["GET"])
@jwt_required()
def get_profiles():
    """
    Get all active profiles for the current user's academy.
    Requires X-Academy-Id header.
    """
    academy_id = request.headers.get("X-Academy-Id")
    if not academy_id:
        return jsonify({"error": "X-Academy-Id header is required"}), 400

    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.academy_id != academy_id:
        return jsonify({"error": "Access denied"}), 403

    profiles = tenant_service.get_academy_profiles(academy_id)
    return jsonify({
        "profiles": [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "picture": p.picture,
                "avatar_color_1": p.avatar_color_1,
                "avatar_color_2": p.avatar_color_2,
            }
            for p in profiles
        ]
    }), 200


@auth_bp.route("/verify-pin", methods=["POST"])
def verify_pin():
    """
    Verify a profile's PIN and return a session token.
    NO JWT required — the PIN itself is the authentication factor.
    Used by the profile picker flow: select profile → enter PIN → dashboard.
    Body: { user_id, pin }
    Returns: { access_token, user_id, name, role, academy_id }
    """
    data = request.get_json()
    if not data or not data.get("user_id") or not data.get("pin"):
        return jsonify({"error": "user_id and pin are required"}), 400

    result = auth_service.authenticate_profile(data["user_id"], data["pin"])
    if not result:
        return jsonify({"error": "Invalid PIN"}), 401

    return jsonify(result), 200


@auth_bp.route("/create-owner", methods=["POST"])
def create_owner():
    """
    Create the first owner profile during academy setup.
    NO JWT required — this is the bootstrap endpoint.
    Body: { academy_id, name, email, password, pin }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("academy_id", "name", "email", "password", "pin")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Validate academy exists
    from app.models.academy import Academy
    academy = db.session.get(Academy, data["academy_id"])
    if not academy:
        return jsonify({"error": "Academy not found"}), 404

    # Check no owner already exists for this academy
    existing_owner = User.query.filter_by(
        academy_id=data["academy_id"], role="owner"
    ).first()
    if existing_owner:
        return jsonify({"error": "Owner already exists for this academy"}), 409

    try:
        owner = tenant_service.create_owner_profile(
            academy_id=data["academy_id"],
            name=data["name"],
            email=data["email"],
            password=data["password"],
            pin=data["pin"],
        )
        db.session.commit()
        return jsonify({
            "id": owner.id,
            "name": owner.name,
            "role": owner.role,
            "academy_id": owner.academy_id,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/create-profile", methods=["POST"])
@jwt_required()
def create_profile():
    """
    Create a new staff/owner profile (owner-only action).
    Body: { name, pin, role?, phone? }
    Requires owner PIN verification.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.role != "owner":
        return jsonify({"error": "Owner access required"}), 403

    # Verify owner PIN
    pin = data.get("owner_pin")
    if not pin or not user.verify_pin(pin):
        return jsonify({"error": "Owner PIN verification required"}), 401

    required = ("name", "pin")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        new_user = tenant_service.create_staff_profile(
            academy_id=user.academy_id,
            name=data["name"],
            pin=data["pin"],
            phone=data.get("phone"),
            role=data.get("role", "staff"),
        )
        db.session.commit()
        return jsonify({
            "id": new_user.id,
            "name": new_user.name,
            "role": new_user.role,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/change-pin", methods=["POST"])
@jwt_required()
def change_pin():
    """
    Change a user's PIN.
    Body: { old_pin, new_pin }
    """
    data = request.get_json()
    if not data or not data.get("old_pin") or not data.get("new_pin"):
        return jsonify({"error": "old_pin and new_pin are required"}), 400

    user_id = get_jwt_identity()
    success = auth_service.change_pin(user_id, data["old_pin"], data["new_pin"])
    if not success:
        return jsonify({"error": "Invalid current PIN"}), 401

    return jsonify({"message": "PIN changed successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get the current authenticated user's profile."""
    user_id = get_jwt_identity()
    user = auth_service.get_current_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "academy_id": user.academy_id,
        "picture": user.picture,
        "is_active": user.is_active,
    }), 200
