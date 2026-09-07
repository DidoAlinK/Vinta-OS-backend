"""
Vinta School OS — Attendance Service
Manual check-in, auto-checkout at class end, popup status.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.attendance import SessionStudent
from app.models.scheduling import Session
from app.models.audit import ActivityLog


def check_in_student(
    session_id: str, student_id: str, academy_id: str, checked_in_by: str
) -> SessionStudent:
    """Mark a student as checked in to a session."""
    record = SessionStudent.query.filter_by(
        session_id=session_id, student_id=student_id
    ).first()

    if record:
        # Update existing record
        record.is_present = True
        record.checked_in_at = datetime.now(timezone.utc)
        record.checked_in_by = checked_in_by
    else:
        # Create new record
        record = SessionStudent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            student_id=student_id,
            is_present=True,
            checked_in_at=datetime.now(timezone.utc),
            checked_in_by=checked_in_by,
            payment_status="paid",
        )
        db.session.add(record)

    # Audit log
    from app.models.student import Student
    student = db.session.get(Student, student_id)
    student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=checked_in_by,
        entity_type="session",
        entity_id=session_id,
        action="checked_in",
        description=f"Student check-in — {student_name}",
    )
    db.session.add(log)
    db.session.flush()

    return record


def check_out_student(
    session_id: str, student_id: str, academy_id: str
) -> SessionStudent | None:
    """Check out a student from a session."""
    record = SessionStudent.query.filter_by(
        session_id=session_id, student_id=student_id
    ).first()

    if not record or not record.is_present:
        return None

    record.checked_out_at = datetime.now(timezone.utc)

    from app.models.student import Student
    student = db.session.get(Student, student_id)
    student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=record.checked_in_by or "system",
        entity_type="session",
        entity_id=session_id,
        action="checked_out",
        description=f"Student check-out — {student_name}",
    )
    db.session.add(log)
    db.session.flush()

    return record


def auto_checkout_session(session_id: str, academy_id: str) -> int:
    """
    Auto check-out all present students when session ends.
    Returns count of students checked out.
    """
    now = datetime.now(timezone.utc)
    records = SessionStudent.query.filter_by(
        session_id=session_id, is_present=True
    ).filter(SessionStudent.checked_out_at.is_(None)).all()

    count = 0
    for record in records:
        record.checked_out_at = now
        count += 1

    if count > 0:
        log = ActivityLog(
            id=str(uuid.uuid4()),
            academy_id=academy_id,
            user_id="system",
            entity_type="session",
            entity_id=session_id,
            action="checked_out",
            description=f"Auto check-out — {count} students",
        )
        db.session.add(log)
        db.session.flush()

    return count


def get_session_roster(session_id: str) -> list:
    """Get the full roster for a session with attendance status."""
    records = SessionStudent.query.filter_by(session_id=session_id).all()

    roster = []
    for record in records:
        student = record.student
        roster.append({
            "id": record.id,
            "student_id": record.student_id,
            "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
            "is_present": record.is_present,
            "checked_in_at": record.checked_in_at.isoformat() if record.checked_in_at else None,
            "checked_out_at": record.checked_out_at.isoformat() if record.checked_out_at else None,
            "checked_in_by": record.checked_in_by,
            "payment_status": record.payment_status,
        })

    return roster


def add_student_to_session(
    session_id: str, student_id: str, academy_id: str, added_by: str
) -> SessionStudent:
    """Add a student to a session roster."""
    existing = SessionStudent.query.filter_by(
        session_id=session_id, student_id=student_id
    ).first()
    if existing:
        return existing

    record = SessionStudent(
        id=str(uuid.uuid4()),
        session_id=session_id,
        student_id=student_id,
        is_present=False,
        payment_status="paid",
    )
    db.session.add(record)

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=added_by,
        entity_type="session",
        entity_id=session_id,
        action="created",
        description="Student added to session",
    )
    db.session.add(log)
    db.session.flush()

    return record
