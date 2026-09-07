"""
Vinta School OS — Billing Service
Cycle renewals, aging buckets (1-7d, 8-30d, 30d+), payment logs, status management.
"""
import uuid
from datetime import date, timedelta
from sqlalchemy import desc, func, extract
from app.extensions import db
from app.models.billing import PaymentPlan, StudentBilling, PaymentLog
from app.models.student import Student
from app.models.audit import ActivityLog
from app.utils.formatters import days_overdue, overdue_bucket


def list_payment_plans(academy_id: str) -> list:
    """List all payment plans for an academy."""
    plans = PaymentPlan.query.filter_by(academy_id=academy_id).order_by(PaymentPlan.amount_da).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "duration_days": p.duration_days,
            "amount_da": p.amount_da,
        }
        for p in plans
    ]


def create_payment_plan(academy_id: str, data: dict) -> PaymentPlan:
    """Create a new payment plan."""
    plan = PaymentPlan(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        name=data["name"],
        duration_days=data["duration_days"],
        amount_da=data["amount_da"],
    )
    db.session.add(plan)
    db.session.flush()
    return plan


def list_student_billings(academy_id: str, student_id: str = None, status: str = None) -> list:
    """List billing records, optionally filtered by student and status."""
    query = StudentBilling.query.join(Student).filter(Student.academy_id == academy_id)

    if student_id:
        query = query.filter(StudentBilling.student_id == student_id)
    if status:
        query = query.filter(StudentBilling.status == status)

    billings = query.order_by(desc(StudentBilling.created_at)).all()

    return [
        {
            "id": b.id,
            "student_id": b.student_id,
            "student_name": f"{b.student.first_name} {b.student.last_name}" if b.student else None,
            "payment_plan": b.payment_plan.name if b.payment_plan else None,
            "amount_da": b.amount_da,
            "status": b.status,
            "due_date": b.due_date.isoformat(),
            "paid_date": b.paid_date.isoformat() if b.paid_date else None,
            "paid_amount": b.paid_amount,
            "cycle_start": b.cycle_start.isoformat(),
            "cycle_end": b.cycle_end.isoformat(),
            "days_overdue": days_overdue(b.due_date) if b.status == "overdue" else 0,
        }
        for b in billings
    ]


def record_payment(
    billing_id: str, amount: int, payment_method: str,
    recorded_by: str, academy_id: str, notes: str = None
) -> dict:
    """Record a payment against a billing record."""
    billing = db.session.get(StudentBilling, billing_id)
    if not billing:
        return None

    # Create payment log
    log_entry = PaymentLog(
        id=str(uuid.uuid4()),
        student_billing_id=billing_id,
        amount_da=amount,
        payment_method=payment_method,
        recorded_by=recorded_by,
        notes=notes,
    )
    db.session.add(log_entry)

    # Update billing
    billing.paid_amount = (billing.paid_amount or 0) + amount
    billing.updated_at = date.today()

    if billing.paid_amount >= billing.amount_da:
        billing.status = "paid"
        billing.paid_date = date.today()

    # Audit log
    student = db.session.get(Student, billing.student_id)
    student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

    audit_log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=recorded_by,
        entity_type="payment",
        entity_id=billing_id,
        action="payment_received",
        description=f"Payment received — {student_name}",
        metadata={"amount": amount, "method": payment_method},
    )
    db.session.add(audit_log)
    db.session.flush()

    return {
        "billing_id": billing_id,
        "amount_paid": amount,
        "total_paid": billing.paid_amount,
        "status": billing.status,
    }


def check_overdue_billings(academy_id: str) -> int:
    """
    Check for billings that are past due_date and mark them as overdue.
    Returns count of newly overdue records.
    """
    today = date.today()
    overdue_billings = StudentBilling.query.join(Student).filter(
        Student.academy_id == academy_id,
        StudentBilling.status == "due",
        StudentBilling.due_date < today,
    ).all()

    count = 0
    for billing in overdue_billings:
        billing.status = "overdue"
        count += 1

        student = db.session.get(Student, billing.student_id)
        student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

        log = ActivityLog(
            id=str(uuid.uuid4()),
            academy_id=academy_id,
            user_id="system",
            entity_type="billing",
            entity_id=billing.id,
            action="payment_overdue",
            description=f"Payment overdue — {student_name}",
        )
        db.session.add(log)

    if count > 0:
        db.session.flush()

    return count


def renew_billing_cycles(academy_id: str) -> int:
    """
    Create new billing records for students whose cycles have ended.
    Returns count of renewals created.
    """
    today = date.today()
    expired = StudentBilling.query.join(Student).filter(
        Student.academy_id == academy_id,
        StudentBilling.cycle_end <= today,
    ).all()

    count = 0
    for billing in expired:
        # Check if a renewal already exists
        existing = StudentBilling.query.filter_by(
            student_id=billing.student_id
        ).filter(
            StudentBilling.cycle_start >= today
        ).first()
        if existing:
            continue

        plan = billing.payment_plan
        if not plan:
            continue

        new_billing = StudentBilling(
            id=str(uuid.uuid4()),
            student_id=billing.student_id,
            payment_plan_id=plan.id,
            amount_da=plan.amount_da,
            status="due",
            due_date=today + timedelta(days=plan.duration_days),
            cycle_start=today,
            cycle_end=today + timedelta(days=plan.duration_days),
        )
        db.session.add(new_billing)
        count += 1

    if count > 0:
        db.session.flush()

    return count


def get_billing_stats(academy_id: str) -> dict:
    """Get aggregate billing statistics for the donut chart."""
    from app.models.teacher import TeacherPayroll

    # Student billing ring
    student_billings = StudentBilling.query.join(Student).filter(
        Student.academy_id == academy_id
    ).all()

    paid = sum(1 for b in student_billings if b.status == "paid")
    due = sum(1 for b in student_billings if b.status == "due")
    overdue = sum(1 for b in student_billings if b.status == "overdue")

    # Teacher payroll ring
    payrolls = TeacherPayroll.query.join(
        Teacher, TeacherPayroll.teacher_id == Teacher.id
    ).filter(Teacher.academy_id == academy_id).all()

    payroll_pending = sum(1 for p in payrolls if p.status == "pending")
    payroll_settled = sum(1 for p in payrolls if p.status == "settled")
    payroll_overdue = sum(1 for p in payrolls if p.status == "overdue")

    return {
        "student_billing": {"paid": paid, "due": due, "overdue": overdue},
        "teacher_payroll": {
            "pending": payroll_pending,
            "settled": payroll_settled,
            "overdue": payroll_overdue,
        },
    }


def get_revenue_chart(academy_id: str, months: int = 6) -> list:
    """
    Generate time-series revenue data for the chart.
    Returns monthly aggregates for the last N months.
    """
    from datetime import datetime
    today = date.today()
    chart_data = []

    for i in range(months - 1, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)

        # Sum of paid amounts this month
        income = (
            db.session.query(func.sum(StudentBilling.amount_da))
            .join(Student)
            .filter(
                Student.academy_id == academy_id,
                StudentBilling.status == "paid",
                StudentBilling.paid_date >= month_start,
                StudentBilling.paid_date <= month_end,
            )
            .scalar() or 0
        )

        overdue_count = (
            StudentBilling.query.join(Student)
            .filter(
                Student.academy_id == academy_id,
                StudentBilling.status == "overdue",
            )
            .count()
        )

        chart_data.append({
            "month": month_start.strftime("%b %Y"),
            "income": int(income),
            "overdue_count": overdue_count,
        })

    return chart_data


def get_aging_buckets(academy_id: str) -> dict:
    """Classify overdue billings into aging buckets."""
    overdue = StudentBilling.query.join(Student).filter(
        Student.academy_id == academy_id,
        StudentBilling.status == "overdue",
    ).all()

    buckets = {"recent": [], "aging": [], "critical": []}
    for billing in overdue:
        days = days_overdue(billing.due_date)
        bucket = overdue_bucket(days)
        student = billing.student
        buckets[bucket].append({
            "id": billing.id,
            "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
            "amount_da": billing.amount_da,
            "days_overdue": days,
        })

    return {
        "recent": {"count": len(buckets["recent"]), "items": buckets["recent"]},
        "aging": {"count": len(buckets["aging"]), "items": buckets["aging"]},
        "critical": {"count": len(buckets["critical"]), "items": buckets["critical"]},
    }
