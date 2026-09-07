"""
Vinta School OS — Route Decorators
@tenant_required, @owner_only, @verify_staff_pin for access control.
"""
from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.extensions import db
from app.models.user import User
from app.models.academy import Academy


def tenant_required(fn):
    """
    Ensures the authenticated user belongs to the academy
    specified in X-Academy-Id header and sets g.current_academy.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "User not found"}, 404

        academy_id = request.headers.get("X-Academy-Id")
        if not academy_id:
            return {"error": "X-Academy-Id header is required"}, 400

        if user.academy_id != academy_id:
            return {"error": "Access denied: not a member of this academy"}, 403

        if not user.is_active:
            return {"error": "Account is deactivated"}, 403

        g.current_user = user
        g.current_academy_id = academy_id

        academy = db.session.get(Academy, academy_id)
        if not academy:
            return {"error": "Academy not found"}, 404

        g.current_academy = academy
        return fn(*args, **kwargs)

    return wrapper


def owner_only(fn):
    """
    Restricts access to owner role only.
    Must be used after @tenant_required.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, user_id)
            if not user:
                return {"error": "User not found"}, 404
            g.current_user = user

        if user.role != "owner":
            return {"error": "Owner access required"}, 403

        return fn(*args, **kwargs)

    return wrapper


def verify_staff_pin(fn):
    """
    Verifies the staff member's PIN before performing a sensitive action.
    Expects JSON body with 'pin' field.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = db.session.get(User, user_id)
            if not user:
                return {"error": "User not found"}, 404
            g.current_user = user

        data = request.get_json() or {}
        pin = data.get("pin")
        if not pin:
            return {"error": "PIN is required"}, 400

        if not user.verify_pin(pin):
            return {"error": "Invalid PIN"}, 401

        return fn(*args, **kwargs)

    return wrapper
