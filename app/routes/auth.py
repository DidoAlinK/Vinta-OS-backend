"""
Vinta School OS — Auth Blueprint
/api/auth — Login, Profile Selection, PIN Verification, Academy Signup
"""
from flask_smorest import Blueprint
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.services import auth_service, tenant_service
from app.schemas.auth import (
    SignupRequestSchema, LoginRequestSchema, VerifyPinRequestSchema,
    CreateOwnerRequestSchema, CreateProfileRequestSchema, ChangePinRequestSchema,
    TokenResponseSchema, SignupResponseSchema, CreateOwnerResponseSchema,
    ProfileResponseSchema, ProfileListResponseSchema, MeResponseSchema,
)
from app.schemas.base import ErrorSchema, MessageSchema

auth_bp = Blueprint("auth", __name__, description="Authentication & profile management")


@auth_bp.route("/signup", methods=["POST"])
@auth_bp.arguments(SignupRequestSchema)
@auth_bp.response(201, SignupResponseSchema)
@auth_bp.doc(responses={400: ("Validation error", ErrorSchema), 500: ("Server error", ErrorSchema)})
def signup(data):
    """Create a new academy (tenant provisioning)
    Creates a new academy with default settings and subscription. Returns the academy ID for the create-owner step.
    """
    try:
        result = tenant_service.create_academy(
            name=data["name"],
            email=data["email"],
            password=data["password"],
        )
        db.session.commit()
        return result, 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
@auth_bp.arguments(LoginRequestSchema)
@auth_bp.response(200, TokenResponseSchema)
@auth_bp.doc(responses={400: ("Validation error", ErrorSchema), 401: ("Invalid credentials", ErrorSchema)})
def login(data):
    """Owner login with email + password
    Authenticates the academy owner and returns JWT tokens. Use the access_token in subsequent requests as `Authorization: Bearer <token>`.
    """
    result = auth_service.authenticate_owner(data["email"], data["password"])
    if not result:
        return jsonify({"error": "Invalid email or password"}), 401
    return result, 200


@auth_bp.route("/profiles", methods=["GET"])
@jwt_required()
@auth_bp.response(200, ProfileListResponseSchema)
@auth_bp.doc(
    security=[{"Bearer": []}],
    parameters=[{"in": "header", "name": "X-Academy-Id", "required": True, "schema": {"type": "string"}, "description": "Academy ID"}],
    responses={400: ("Missing academy header", ErrorSchema), 403: ("Access denied", ErrorSchema)},
)
def get_profiles():
    """Get all active profiles for the academy
    Returns all user profiles (owner + staff) for the profile picker screen. Requires JWT and X-Academy-Id header.
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
@auth_bp.arguments(VerifyPinRequestSchema)
@auth_bp.response(200, TokenResponseSchema)
@auth_bp.doc(
    parameters=[{"in": "header", "name": "X-Academy-Id", "required": True, "schema": {"type": "string"}, "description": "Academy ID — validates the profile belongs to this academy"}],
    responses={400: ("Missing header", ErrorSchema), 401: ("Invalid PIN or profile", ErrorSchema)},
)
def verify_pin(data):
    """Verify a profile's PIN and return a session token
    **No JWT required** — the PIN itself is the authentication factor. Used by the profile picker flow: select profile → enter PIN → dashboard. Requires X-Academy-Id header to prevent cross-academy PIN enumeration.
    """
    academy_id = request.headers.get("X-Academy-Id")
    if not academy_id:
        return jsonify({"error": "X-Academy-Id header is required"}), 400

    user = db.session.get(User, data["user_id"])
    if not user or user.academy_id != academy_id:
        return jsonify({"error": "Profile not found"}), 401

    result = auth_service.authenticate_profile(data["user_id"], data["pin"])
    if not result:
        return jsonify({"error": "Invalid PIN"}), 401

    return result, 200


@auth_bp.route("/create-owner", methods=["POST"])
@auth_bp.arguments(CreateOwnerRequestSchema)
@auth_bp.response(201, CreateOwnerResponseSchema)
@auth_bp.doc(
    parameters=[{"in": "header", "name": "X-Academy-Id", "required": True, "schema": {"type": "string"}, "description": "Must match body academy_id"}],
    responses={400: ("Validation error", ErrorSchema), 404: ("Academy not found", ErrorSchema), 409: ("Owner already exists", ErrorSchema)},
)
def create_owner(data):
    """Create the first owner profile during academy setup
    **No JWT required** — this is the bootstrap endpoint called after academy signup. Requires X-Academy-Id header matching the body academy_id. Can only be called once per academy (409 if owner exists).
    """
    academy_id = request.headers.get("X-Academy-Id")
    if not academy_id:
        return jsonify({"error": "X-Academy-Id header is required"}), 400
    if academy_id != data["academy_id"]:
        return jsonify({"error": "X-Academy-Id header does not match body"}), 400

    from app.models.academy import Academy
    academy = db.session.get(Academy, data["academy_id"])
    if not academy:
        return jsonify({"error": "Academy not found"}), 404

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
@auth_bp.arguments(CreateProfileRequestSchema)
@auth_bp.response(201, ProfileResponseSchema)
@auth_bp.doc(
    security=[{"Bearer": []}],
    responses={400: ("Validation error", ErrorSchema), 401: ("PIN required", ErrorSchema), 403: ("Owner access required", ErrorSchema)},
)
def create_profile(data):
    """Create a new staff/owner profile (owner-only action)
    Creates a new user profile with PIN for the profile picker. Requires JWT (owner role) and owner PIN verification in the request body.
    """
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    if not user or user.role != "owner":
        return jsonify({"error": "Owner access required"}), 403

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
@auth_bp.arguments(ChangePinRequestSchema)
@auth_bp.response(200, MessageSchema)
@auth_bp.doc(security=[{"Bearer": []}], responses={400: ("Validation error", ErrorSchema), 401: ("Invalid PIN", ErrorSchema)})
def change_pin(data):
    """Change the current user's PIN
    Requires JWT. Must provide old PIN for verification and new PIN.
    """
    user_id = get_jwt_identity()
    success = auth_service.change_pin(user_id, data["old_pin"], data["new_pin"])
    if not success:
        return jsonify({"error": "Invalid current PIN"}), 401
    return jsonify({"message": "PIN changed successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
@auth_bp.response(200, MeResponseSchema)
@auth_bp.doc(security=[{"Bearer": []}], responses={404: ("User not found", ErrorSchema)})
def get_current_user():
    """Get the current authenticated user's profile
    Requires JWT. Returns full profile details for the authenticated user.
    """
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
