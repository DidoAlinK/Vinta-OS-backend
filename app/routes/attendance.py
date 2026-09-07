"""
Vinta School OS — Attendance Blueprint
/api/attendance — Check-in/out, PIN attribution
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required, verify_staff_pin
from app.services import attendance_service

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/check-in", methods=["POST"])
@jwt_required()
@tenant_required
@verify_staff_pin
def check_in():
    """
    Mark a student as checked in to a session.
    Body: { session_id, student_id, pin }
    PIN is verified by @verify_staff_pin decorator — action is attributed to the PIN holder.
    """
    from flask import g
    data = request.get_json()

    record = attendance_service.check_in_student(
        session_id=data["session_id"],
        student_id=data["student_id"],
        academy_id=g.current_academy_id,
        checked_in_by=g.current_user.id,
    )
    db.session.commit()

    return jsonify({
        "id": record.id,
        "student_id": record.student_id,
        "is_present": record.is_present,
        "checked_in_at": record.checked_in_at.isoformat() if record.checked_in_at else None,
        "checked_in_by": record.checked_in_by,
    }), 200


@attendance_bp.route("/check-out", methods=["POST"])
@jwt_required()
@tenant_required
def check_out():
    """
    Check out a student from a session.
    Body: { session_id, student_id }
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("session_id") or not data.get("student_id"):
        return jsonify({"error": "session_id and student_id are required"}), 400

    record = attendance_service.check_out_student(
        data["session_id"], data["student_id"], g.current_academy_id
    )
    if not record:
        return jsonify({"error": "Student not checked in or not found"}), 404

    db.session.commit()
    return jsonify({
        "id": record.id,
        "student_id": record.student_id,
        "checked_out_at": record.checked_out_at.isoformat() if record.checked_out_at else None,
    }), 200


@attendance_bp.route("/auto-checkout", methods=["POST"])
@jwt_required()
@tenant_required
def auto_checkout():
    """
    Trigger auto check-out for all present students in a session.
    Body: { session_id }
    Called by cron job at scheduled class end time.
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("session_id"):
        return jsonify({"error": "session_id is required"}), 400

    count = attendance_service.auto_checkout_session(
        data["session_id"], g.current_academy_id
    )
    db.session.commit()

    return jsonify({
        "session_id": data["session_id"],
        "checked_out_count": count,
    }), 200


@attendance_bp.route("/roster/<session_id>", methods=["GET"])
@jwt_required()
@tenant_required
def get_roster(session_id):
    """Get the full roster for a session with attendance status."""
    roster = attendance_service.get_session_roster(session_id)
    return jsonify({"roster": roster}), 200


@attendance_bp.route("/add-to-session", methods=["POST"])
@jwt_required()
@tenant_required
def add_to_session():
    """
    Add a student to a session roster.
    Body: { session_id, student_id }
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("session_id") or not data.get("student_id"):
        return jsonify({"error": "session_id and student_id are required"}), 400

    record = attendance_service.add_student_to_session(
        data["session_id"], data["student_id"],
        g.current_academy_id, g.current_user.id,
    )
    db.session.commit()

    return jsonify({
        "id": record.id,
        "student_id": record.student_id,
        "is_present": record.is_present,
    }), 201
