"""
Vinta School OS — Payroll Service
Hourly vs. Per-student contract calculations, monthly payroll generation.
"""
import uuid
from datetime import date, timedelta
from sqlalchemy import func, desc
from app.extensions import db
from app.models.teacher import Teacher, TeacherPayroll, TeacherHoursLog
from app.models.student import Student, Enrollment
from app.models.scheduling import Session
from app.models.audit import ActivityLog


def calculate_teacher_payroll(teacher_id: str, period_start: date, period_end: date) -> dict:
    """
    Calculate payroll for a teacher for a given period.
    Hourly: total_hours × hourly_rate
    Per-student: active_students × per_student_rate
    """
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return None

    if teacher.contract_type == "hourly":
        total_hours = (
            db.session.query(func.sum(TeacherHoursLog.hours))
            .filter(
                TeacherHoursLog.teacher_id == teacher_id,
                TeacherHoursLog.created_at >= period_start,
                TeacherHoursLog.created_at <= period_end,
            )
            .scalar() or 0
        )
        rate = teacher.hourly_rate or 0
        calculated_amount = int(float(total_hours) * rate)

        return {
            "teacher_id": teacher_id,
            "contract_type": "hourly",
            "total_hours": float(total_hours),
            "total_students": 0,
            "rate_applied": rate,
            "calculated_amount": calculated_amount,
        }
    else:
        # Per-student: count active enrollments in classes taught by this teacher
        active_students = (
            db.session.query(func.count(func.distinct(Enrollment.student_id)))
            .join(Student, Enrollment.student_id == Student.id)
            .filter(
                Student.academy_id == teacher.academy_id,
                Enrollment.status == "active",
                Enrollment.class_id.in_(
                    db.session.query(Session.class_id).filter(
                        Session.teacher_id == teacher_id
                    ).distinct()
                ),
            )
            .scalar() or 0
        )
        rate = teacher.per_student_rate or 0
        calculated_amount = int(active_students * rate)

        return {
            "teacher_id": teacher_id,
            "contract_type": "per_student",
            "total_hours": 0,
            "total_students": active_students,
            "rate_applied": rate,
            "calculated_amount": calculated_amount,
        }


def generate_monthly_payroll(academy_id: str, year: int, month: int) -> int:
    """
    Generate payroll records for all teachers in an academy for a given month.
    Returns count of payroll records created.
    """
    period_start = date(year, month, 1)
    if month == 12:
        period_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        period_end = date(year, month + 1, 1) - timedelta(days=1)

    teachers = Teacher.query.filter_by(academy_id=academy_id).all()
    count = 0

    for teacher in teachers:
        # Skip if payroll already exists for this period
        existing = TeacherPayroll.query.filter_by(
            teacher_id=teacher.id,
            period_start=period_start,
        ).first()
        if existing:
            continue

        calc = calculate_teacher_payroll(teacher.id, period_start, period_end)
        if not calc:
            continue

        payroll = TeacherPayroll(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            period_start=period_start,
            period_end=period_end,
            total_hours=calc["total_hours"],
            total_students=calc["total_students"],
            rate_applied=calc["rate_applied"],
            calculated_amount=calc["calculated_amount"],
            status="pending",
        )
        db.session.add(payroll)
        count += 1

    if count > 0:
        db.session.flush()

    return count


def settle_payroll(payroll_id: str, academy_id: str, settled_by: str) -> bool:
    """Mark a payroll record as settled (paid)."""
    payroll = db.session.get(TeacherPayroll, payroll_id)
    if not payroll:
        return False

    teacher = db.session.get(Teacher, payroll.teacher_id)
    if not teacher or teacher.academy_id != academy_id:
        return False

    payroll.status = "settled"
    payroll.paid_date = date.today()

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=settled_by,
        entity_type="teacher",
        entity_id=payroll.teacher_id,
        action="payment_received",
        description=f"Payroll settled — {teacher.full_name}",
        metadata={"amount": payroll.calculated_amount, "period": str(payroll.period_start)},
    )
    db.session.add(log)
    db.session.flush()

    return True


def log_teacher_hours(
    teacher_id: str, session_id: str, hours: float, logged_by: str
) -> TeacherHoursLog:
    """Log hours for a teacher's session."""
    log_entry = TeacherHoursLog(
        id=str(uuid.uuid4()),
        teacher_id=teacher_id,
        session_id=session_id,
        hours=hours,
        logged_by=logged_by,
    )
    db.session.add(log_entry)
    db.session.flush()

    return log_entry


def list_teacher_payrolls(academy_id: str, teacher_id: str = None) -> list:
    """List payroll records for a teacher or all teachers in an academy."""
    query = TeacherPayroll.query.join(Teacher).filter(Teacher.academy_id == academy_id)

    if teacher_id:
        query = query.filter(TeacherPayroll.teacher_id == teacher_id)

    payrolls = query.order_by(desc(TeacherPayroll.period_start)).all()

    return [
        {
            "id": p.id,
            "teacher_id": p.teacher_id,
            "teacher_name": p.teacher.full_name if p.teacher else None,
            "period_start": p.period_start.isoformat(),
            "period_end": p.period_end.isoformat(),
            "total_hours": float(p.total_hours),
            "total_students": p.total_students,
            "rate_applied": p.rate_applied,
            "calculated_amount": p.calculated_amount,
            "status": p.status,
            "paid_date": p.paid_date.isoformat() if p.paid_date else None,
        }
        for p in payrolls
    ]


def get_teacher_summary(teacher_id: str, academy_id: str) -> dict:
    """Get payroll summary for a teacher profile drawer."""
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher or teacher.academy_id != academy_id:
        return None

    # Current month payroll
    today = date.today()
    current_month_start = today.replace(day=1)
    current = TeacherPayroll.query.filter_by(
        teacher_id=teacher_id, period_start=current_month_start
    ).first()

    # This week's hours
    week_start = today - timedelta(days=today.weekday() + 1)  # Sunday
    week_hours = (
        db.session.query(func.sum(TeacherHoursLog.hours))
        .filter(
            TeacherHoursLog.teacher_id == teacher_id,
            TeacherHoursLog.created_at >= week_start,
        )
        .scalar() or 0
    )

    # Active students count (for per-student contracts)
    active_students = 0
    if teacher.contract_type == "per_student":
        active_students = (
            db.session.query(func.count(func.distinct(Enrollment.student_id)))
            .join(Student, Enrollment.student_id == Student.id)
            .filter(
                Student.academy_id == academy_id,
                Enrollment.status == "active",
            )
            .scalar() or 0
        )

    return {
        "teacher_id": teacher_id,
        "contract_type": teacher.contract_type,
        "hourly_rate": teacher.hourly_rate,
        "per_student_rate": teacher.per_student_rate,
        "current_payroll": {
            "calculated_amount": current.calculated_amount if current else 0,
            "status": current.status if current else "pending",
            "total_hours": float(current.total_hours) if current else 0,
            "total_students": current.total_students if current else 0,
        },
        "hours_this_week": float(week_hours),
        "active_students": active_students,
    }
