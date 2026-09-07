"""
Vinta School OS — Students Blueprint
/api/students — CRUD, Guardians, Profile Drawer, Enrollment
"""
from flask_smorest import Blueprint
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required
from app.services import student_service
from app.schemas.students import (
    CreateStudentRequestSchema, UpdateStudentRequestSchema, EnrollStudentRequestSchema,
    AddGuardianRequestSchema, StudentListResponseSchema, StudentStatsResponseSchema,
    StudentProfileResponseSchema, CreateStudentResponseSchema, EnrollResponseSchema,
)
from app.schemas.base import ErrorSchema, MessageSchema

students_bp = Blueprint("students", __name__, description="Student management")


@students_bp.route("", methods=["GET"])
@jwt_required()
@tenant_required
def list_students():
    """
    List all students for the academy with computed status fields.
    Query params: page, per_page
    """
    from flask import g
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    result = student_service.list_students(g.current_academy_id, page, per_page)
    return jsonify(result), 200


@students_bp.route("/stats", methods=["GET"])
@jwt_required()
@tenant_required
def get_stats():
    """Get aggregate student statistics for the stats rail."""
    from flask import g
    stats = student_service.get_student_stats(g.current_academy_id)
    return jsonify(stats), 200


@students_bp.route("/<student_id>", methods=["GET"])
@jwt_required()
@tenant_required
def get_student(student_id):
    """Get a single student with all related data (profile drawer)."""
    from flask import g
    result = student_service.get_student(student_id, g.current_academy_id)
    if not result:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(result), 200


@students_bp.route("", methods=["POST"])
@jwt_required()
@tenant_required
def create_student():
    """
    Create a new student with default guardian and billing.
    Body: { first_name, last_name, phone?, parent_phone?, notes? }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if not data.get("first_name") or not data.get("last_name"):
        return jsonify({"error": "first_name and last_name are required"}), 400

    try:
        student = student_service.create_student(
            academy_id=g.current_academy_id,
            data=data,
            created_by=g.current_user.id,
        )
        db.session.commit()
        return jsonify({
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "full_name": student.full_name,
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@students_bp.route("/<student_id>", methods=["PUT"])
@jwt_required()
@tenant_required
def update_student(student_id):
    """Update student profile fields."""
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    student = student_service.update_student(student_id, g.current_academy_id, data)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    db.session.commit()
    return jsonify({
        "id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
    }), 200


@students_bp.route("/<student_id>", methods=["DELETE"])
@jwt_required()
@tenant_required
def delete_student(student_id):
    """Delete student and cascade withdraw enrollments."""
    from flask import g
    success = student_service.delete_student(
        student_id, g.current_academy_id, g.current_user.id
    )
    if not success:
        return jsonify({"error": "Student not found"}), 404

    db.session.commit()
    return jsonify({"message": "Student deleted"}), 200


@students_bp.route("/<student_id>/enroll", methods=["POST"])
@jwt_required()
@tenant_required
def enroll_student(student_id):
    """
    Enroll a student in a class.
    Body: { class_id }
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("class_id"):
        return jsonify({"error": "class_id is required"}), 400

    enrollment = student_service.enroll_student(
        student_id, data["class_id"], g.current_academy_id, g.current_user.id
    )
    db.session.commit()

    return jsonify({
        "id": enrollment.id,
        "student_id": enrollment.student_id,
        "class_id": enrollment.class_id,
        "status": enrollment.status,
    }), 201


@students_bp.route("/<student_id>/guardians", methods=["GET"])
@jwt_required()
@tenant_required
def list_guardians(student_id):
    """List guardians for a student."""
    from flask import g
    from app.models.student import Student, Guardian

    student = Student.query.filter_by(id=student_id, academy_id=g.current_academy_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    guardians = Guardian.query.filter_by(student_id=student_id).all()
    return jsonify({
        "guardians": [
            {
                "id": g.id,
                "name": g.name,
                "relationship": g.relationship_type,
                "phone": g.phone,
                "is_emergency": g.is_emergency,
            }
            for g in guardians
        ]
    }), 200


@students_bp.route("/<student_id>/guardians", methods=["POST"])
@jwt_required()
@tenant_required
def add_guardian(student_id):
    """
    Add a guardian to a student.
    Body: { name, relationship, phone, is_emergency? }
    """
    from flask import g
    import uuid
    from app.models.student import Student, Guardian

    student = Student.query.filter_by(id=student_id, academy_id=g.current_academy_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json()
    if not data or not data.get("name") or not data.get("phone"):
        return jsonify({"error": "name and phone are required"}), 400

    guardian = Guardian(
        id=str(uuid.uuid4()),
        student_id=student_id,
        name=data["name"],
        relationship_type=data.get("relationship"),
        phone=data["phone"],
        is_emergency=data.get("is_emergency", False),
    )
    db.session.add(guardian)
    db.session.commit()

    return jsonify({
        "id": guardian.id,
        "name": guardian.name,
        "relationship": guardian.relationship_type,
        "phone": guardian.phone,
    }), 201
