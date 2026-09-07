"""
Vinta School OS — Student Service
Enrollment, status derivation (paid/due/overdue), CRUD operations.
"""
import uuid
from datetime import date, timedelta
from sqlalchemy import desc
from app.extensions import db
from app.models.student import Student, Guardian, Enrollment
from app.models.billing import StudentBilling, PaymentPlan
from app.models.audit import ActivityLog


def list_students(academy_id: str, page: int = 1, per_page: int = 50) -> dict:
    """List all students for an academy with computed status fields."""
    query = Student.query.filter_by(academy_id=academy_id)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    students = []
    for student in pagination.items:
        student_data = _enrich_student(student)
        students.append(student_data)

    return {
        "students": students,
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
    }


def get_student(student_id: str, academy_id: str) -> dict | None:
    """Get a single student with all related data."""
    student = Student.query.filter_by(id=student_id, academy_id=academy_id).first()
    if not student:
        return None

    data = _enrich_student(student)
    data["guardians"] = [
        {
            "id": g.id,
            "name": g.name,
            "relationship": g.relationship_type,
            "phone": g.phone,
            "is_emergency": g.is_emergency,
        }
        for g in student.guardians
    ]
    data["enrollments"] = [
        {
            "id": e.id,
            "class_id": e.class_id,
            "class_name": e.class_.name if e.class_ else None,
            "status": e.status,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        }
        for e in student.enrollments.filter_by(status="active").all()
    ]
    data["billing_calendar"] = _get_billing_calendar(student.id)

    return data


def create_student(academy_id: str, data: dict, created_by: str) -> Student:
    """Create a new student with default guardian and billing."""
    student = Student(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data.get("phone"),
        parent_phone=data.get("parent_phone"),
        notes=data.get("notes"),
    )
    db.session.add(student)
    db.session.flush()

    # Default guardian
    guardian = Guardian(
        id=str(uuid.uuid4()),
        student_id=student.id,
        name="Parent",
        relationship="Parent",
        phone=data.get("parent_phone", ""),
        is_emergency=True,
    )
    db.session.add(guardian)

    # Default billing (status=paid, 0 sessions)
    default_plan = PaymentPlan.query.filter_by(
        academy_id=academy_id
    ).order_by(PaymentPlan.amount_da.desc()).first()

    if default_plan:
        today = date.today()
        billing = StudentBilling(
            id=str(uuid.uuid4()),
            student_id=student.id,
            payment_plan_id=default_plan.id,
            amount_da=0,
            status="paid",
            due_date=today,
            paid_date=today,
            paid_amount=0,
            cycle_start=today,
            cycle_end=today + timedelta(days=default_plan.duration_days),
        )
        db.session.add(billing)

    # Audit log
    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=created_by,
        entity_type="student",
        entity_id=student.id,
        action="created",
        description=f"New student enrolled — {student.first_name} {student.last_name}",
    )
    db.session.add(log)
    db.session.flush()

    return student


def update_student(student_id: str, academy_id: str, data: dict) -> Student | None:
    """Update student profile fields."""
    student = Student.query.filter_by(id=student_id, academy_id=academy_id).first()
    if not student:
        return None

    for field in ("first_name", "last_name", "phone", "parent_phone", "notes"):
        if field in data:
            setattr(student, field, data[field])

    db.session.flush()
    return student


def delete_student(student_id: str, academy_id: str, deleted_by: str) -> bool:
    """Soft-delete student and cascade withdraw enrollments."""
    student = Student.query.filter_by(id=student_id, academy_id=academy_id).first()
    if not student:
        return False

    # Withdraw all active enrollments
    enrollments = Enrollment.query.filter_by(student_id=student_id, status="active").all()
    for enrollment in enrollments:
        enrollment.status = "withdrawn"

    # Audit log
    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=deleted_by,
        entity_type="student",
        entity_id=student_id,
        action="deleted",
        description=f"Student profile removed — {student.first_name} {student.last_name}",
    )
    db.session.add(log)

    db.session.delete(student)
    db.session.flush()
    return True


def enroll_student(student_id: str, class_id: str, academy_id: str, enrolled_by: str) -> Enrollment:
    """Enroll a student in a class."""
    # Check if already enrolled
    existing = Enrollment.query.filter_by(
        student_id=student_id, class_id=class_id, status="active"
    ).first()
    if existing:
        return existing

    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        student_id=student_id,
        class_id=class_id,
        status="active",
    )
    db.session.add(enrollment)

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=enrolled_by,
        entity_type="student",
        entity_id=student_id,
        action="enrolled",
        description="Student enrolled in class",
    )
    db.session.add(log)
    db.session.flush()

    return enrollment


def get_student_stats(academy_id: str) -> dict:
    """Get aggregate student statistics for the stats rail."""
    total = Student.query.filter_by(academy_id=academy_id).count()

    # Derive paid/overdue from latest billing
    paid = 0
    overdue = 0
    students = Student.query.filter_by(academy_id=academy_id).all()
    for student in students:
        latest_billing = (
            StudentBilling.query.filter_by(student_id=student.id)
            .order_by(desc(StudentBilling.created_at))
            .first()
        )
        if latest_billing:
            if latest_billing.status == "paid":
                paid += 1
            elif latest_billing.status == "overdue":
                overdue += 1
        else:
            paid += 1  # Default if no billing records

    return {"total": total, "paid": paid, "overdue": overdue, "due": total - paid - overdue}


# --- Private Helpers ---

def _enrich_student(student: Student) -> dict:
    """Enrich a student with computed fields."""
    latest_billing = (
        StudentBilling.query.filter_by(student_id=student.id)
        .order_by(desc(StudentBilling.created_at))
        .first()
    )
    status = "paid"
    plan_name = None
    plan_amount = None
    renews = None

    if latest_billing:
        status = latest_billing.status
        if latest_billing.payment_plan:
            plan_name = latest_billing.payment_plan.name
            plan_amount = latest_billing.payment_plan.amount_da

        if status != "paid":
            days = (latest_billing.due_date - date.today()).days
            if days < 0:
                renews = f"overdue {abs(days)}d"
            else:
                renews = f"{days}d"
        else:
            days = (latest_billing.cycle_end - date.today()).days
            renews = f"{days}d" if days > 0 else "today"

    # Enrolled classes
    enrollments = Enrollment.query.filter_by(student_id=student.id, status="active").all()
    classes_str = ", ".join([e.class_.name for e in enrollments if e.class_])

    return {
        "id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "full_name": student.full_name,
        "phone": student.phone,
        "parent_phone": student.parent_phone,
        "notes": student.notes,
        "status": status,
        "classes": classes_str,
        "plan": plan_name,
        "plan_amount": plan_amount,
        "renews": renews,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    }


def _get_billing_calendar(student_id: str) -> list:
    """Get last 4 weeks of billing data for the mini-calendar."""
    from datetime import timedelta
    four_weeks_ago = date.today() - timedelta(weeks=4)

    billings = (
        StudentBilling.query.filter(
            StudentBilling.student_id == student_id,
            StudentBilling.cycle_start >= four_weeks_ago,
        )
        .order_by(StudentBilling.cycle_start)
        .all()
    )

    return [
        {
            "id": b.id,
            "status": b.status,
            "cycle_start": b.cycle_start.isoformat(),
            "cycle_end": b.cycle_end.isoformat(),
            "amount_da": b.amount_da,
            "paid_amount": b.paid_amount,
        }
        for b in billings
    ]
