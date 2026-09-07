"""
Vinta School OS — Classes Blueprint
/api/classes, /api/classrooms — Class & Classroom CRUD, Schedules
"""
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required
from app.models.class_room import Classroom, Class, Subject
from app.models.scheduling import Schedule
from app.services import scheduling_service

classes_bp = Blueprint("classes", __name__)


# ── Classrooms ──────────────────────────────────────────────────────

@classes_bp.route("/classrooms", methods=["GET"])
@jwt_required()
@tenant_required
def list_classrooms():
    """List all classrooms for the academy."""
    from flask import g
    rooms = Classroom.query.filter_by(academy_id=g.current_academy_id).all()
    return jsonify({
        "classrooms": [
            {"id": r.id, "name": r.name, "capacity": r.capacity}
            for r in rooms
        ]
    }), 200


@classes_bp.route("/classrooms", methods=["POST"])
@jwt_required()
@tenant_required
def create_classroom():
    """Create a new classroom. Body: { name, capacity? }"""
    from flask import g
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    room = Classroom(
        id=str(uuid.uuid4()),
        academy_id=g.current_academy_id,
        name=data["name"],
        capacity=data.get("capacity", 0),
    )
    db.session.add(room)
    db.session.commit()
    return jsonify({"id": room.id, "name": room.name, "capacity": room.capacity}), 201


# ── Classes ─────────────────────────────────────────────────────────

@classes_bp.route("/classes", methods=["GET"])
@jwt_required()
@tenant_required
def list_classes():
    """List all classes with enrollment status dots."""
    from flask import g
    from app.models.student import Enrollment

    classes = Class.query.filter_by(academy_id=g.current_academy_id).all()

    result = []
    for cls in classes:
        enrolled_count = Enrollment.query.filter_by(
            class_id=cls.id, status="active"
        ).count()

        # Status dot logic: Red=full, Green=has students, Grey=empty
        if enrolled_count >= cls.capacity and cls.capacity > 0:
            status_color = "red"
        elif enrolled_count > 0:
            status_color = "green"
        else:
            status_color = "grey"

        result.append({
            "id": cls.id,
            "name": cls.name,
            "subject": cls.subject,
            "color": cls.color,
            "teacher_id": cls.teacher_id,
            "teacher_name": cls.teacher.full_name if cls.teacher else "Unassigned",
            "capacity": cls.capacity,
            "enrolled_count": enrolled_count,
            "status_color": status_color,
            "notes": cls.notes,
        })

    return jsonify({"classes": result}), 200


@classes_bp.route("/classes/<class_id>", methods=["GET"])
@jwt_required()
@tenant_required
def get_class(class_id):
    """Get a single class with schedules and enrollment."""
    from flask import g
    from app.models.student import Enrollment

    cls = Class.query.filter_by(id=class_id, academy_id=g.current_academy_id).first()
    if not cls:
        return jsonify({"error": "Class not found"}), 404

    enrolled_count = Enrollment.query.filter_by(
        class_id=cls.id, status="active"
    ).count()

    schedules = Schedule.query.filter_by(class_id=cls.id).all()
    schedule_data = [
        {
            "id": s.id,
            "day_of_week": s.day_of_week,
            "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"),
            "classroom_id": s.classroom_id,
            "classroom_name": s.classroom.name if s.classroom else None,
        }
        for s in schedules
    ]

    return jsonify({
        "id": cls.id,
        "name": cls.name,
        "subject": cls.subject,
        "color": cls.color,
        "teacher_id": cls.teacher_id,
        "teacher_name": cls.teacher.full_name if cls.teacher else "Unassigned",
        "capacity": cls.capacity,
        "enrolled_count": enrolled_count,
        "notes": cls.notes,
        "schedules": schedule_data,
    }), 200


@classes_bp.route("/classes", methods=["POST"])
@jwt_required()
@tenant_required
def create_class():
    """
    Create a new class.
    Body: { name, subject?, color?, teacher_id?, capacity?, notes? }
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    cls = Class(
        id=str(uuid.uuid4()),
        academy_id=g.current_academy_id,
        name=data["name"],
        subject=data.get("subject"),
        color=data.get("color"),
        teacher_id=data.get("teacher_id"),
        capacity=data.get("capacity", 30),
        notes=data.get("notes"),
    )
    db.session.add(cls)
    db.session.commit()

    return jsonify({
        "id": cls.id,
        "name": cls.name,
        "subject": cls.subject,
    }), 201


@classes_bp.route("/classes/<class_id>", methods=["PUT"])
@jwt_required()
@tenant_required
def update_class(class_id):
    """Update class fields."""
    from flask import g

    cls = Class.query.filter_by(id=class_id, academy_id=g.current_academy_id).first()
    if not cls:
        return jsonify({"error": "Class not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    for field in ("name", "subject", "color", "teacher_id", "capacity", "notes"):
        if field in data:
            setattr(cls, field, data[field])

    db.session.commit()
    return jsonify({"id": cls.id, "name": cls.name}), 200


@classes_bp.route("/classes/<class_id>", methods=["DELETE"])
@jwt_required()
@tenant_required
def delete_class(class_id):
    """Delete class, cascade delete schedules, withdraw enrollments."""
    from flask import g
    from app.models.student import Enrollment

    cls = Class.query.filter_by(id=class_id, academy_id=g.current_academy_id).first()
    if not cls:
        return jsonify({"error": "Class not found"}), 404

    # Withdraw all enrollments
    enrollments = Enrollment.query.filter_by(class_id=class_id, status="active").all()
    for e in enrollments:
        e.status = "withdrawn"

    db.session.delete(cls)
    db.session.commit()
    return jsonify({"message": "Class deleted"}), 200


# ── Schedules (within a class) ──────────────────────────────────────

@classes_bp.route("/classes/<class_id>/schedules", methods=["POST"])
@jwt_required()
@tenant_required
def create_schedule(class_id):
    """
    Add a schedule block to a class.
    Body: { day_of_week, start_time, end_time, classroom_id? }
    """
    from flask import g
    from app.utils.formatters import snap_time_obj, _parse_time

    cls = Class.query.filter_by(id=class_id, academy_id=g.current_academy_id).first()
    if not cls:
        return jsonify({"error": "Class not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("day_of_week", "start_time", "end_time")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    schedule = Schedule(
        id=str(uuid.uuid4()),
        class_id=class_id,
        classroom_id=data.get("classroom_id"),
        day_of_week=data["day_of_week"],
        start_time=snap_time_obj(scheduling_service._parse_time(data["start_time"])),
        end_time=snap_time_obj(scheduling_service._parse_time(data["end_time"])),
    )
    db.session.add(schedule)
    db.session.commit()

    # Generate sessions for the next 12 weeks
    sessions_created = scheduling_service.generate_sessions_from_schedule(schedule.id)
    db.session.commit()

    return jsonify({
        "id": schedule.id,
        "day_of_week": schedule.day_of_week,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M"),
        "sessions_created": sessions_created,
    }), 201


@classes_bp.route("/classes/<class_id>/schedules/<schedule_id>", methods=["DELETE"])
@jwt_required()
@tenant_required
def delete_schedule(class_id, schedule_id):
    """Delete a schedule block."""
    from flask import g

    schedule = Schedule.query.filter_by(
        id=schedule_id, class_id=class_id
    ).first()
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({"message": "Schedule deleted"}), 200


# ── Subjects (extensible palette) ───────────────────────────────────

@classes_bp.route("/subjects", methods=["GET"])
@jwt_required()
@tenant_required
def list_subjects():
    """List all subjects for the calendar palette."""
    from flask import g
    subjects = Subject.query.filter_by(academy_id=g.current_academy_id).all()

    # Also include unique subjects from classes
    classes = Class.query.filter_by(academy_id=g.current_academy_id).all()
    seen = {s.name for s in subjects}
    palette = [
        {"name": s.name, "color": s.color} for s in subjects
    ]

    for cls in classes:
        if cls.subject and cls.subject not in seen:
            seen.add(cls.subject)
            palette.append({"name": cls.subject, "color": cls.color or "#b3872a"})

    return jsonify({"subjects": palette}), 200


@classes_bp.route("/subjects", methods=["POST"])
@jwt_required()
@tenant_required
def create_subject():
    """
    Add a custom subject to the palette.
    Body: { name, color }
    """
    from flask import g
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    subject = Subject(
        id=str(uuid.uuid4()),
        academy_id=g.current_academy_id,
        name=data["name"],
        color=data.get("color", "#b3872a"),
    )
    db.session.add(subject)
    db.session.commit()
    return jsonify({"name": subject.name, "color": subject.color}), 201
