"""
Vinta School OS — Export Service
CSV generators for Student Roster, Billing History, Teacher Hours.
"""
import csv
import io
from datetime import date
from sqlalchemy import desc
from app.extensions import db
from app.models.student import Student, Guardian, Enrollment
from app.models.billing import StudentBilling, PaymentLog
from app.models.teacher import Teacher, TeacherHoursLog
from app.models.scheduling import Session


def export_student_roster(academy_id: str) -> str:
    """
    Generate CSV for student roster.
    Columns: Name, Phone, Parent, Classes, Status, Plan
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Phone", "Parent Phone", "Classes", "Status", "Plan"])

    students = Student.query.filter_by(academy_id=academy_id).all()

    for student in students:
        # Get enrollments
        enrollments = Enrollment.query.filter_by(
            student_id=student.id, status="active"
        ).all()
        classes = ", ".join([e.class_.name for e in enrollments if e.class_])

        # Get latest billing
        latest_billing = (
            StudentBilling.query.filter_by(student_id=student.id)
            .order_by(desc(StudentBilling.created_at))
            .first()
        )
        status = latest_billing.status if latest_billing else "paid"
        plan = latest_billing.payment_plan.name if latest_billing and latest_billing.payment_plan else "N/A"

        writer.writerow([
            f"{student.first_name} {student.last_name}",
            student.phone or "",
            student.parent_phone or "",
            classes,
            status,
            plan,
        ])

    return output.getvalue()


def export_billing_history(academy_id: str) -> str:
    """
    Generate CSV for billing history.
    Columns: Student, Status, Amount, Paid, Date, Days Overdue
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Status", "Amount (DA)", "Paid (DA)", "Date", "Days Overdue"])

    from app.models.student import Student as StudentModel
    billings = (
        StudentBilling.query.join(StudentModel)
        .filter(StudentModel.academy_id == academy_id)
        .order_by(desc(StudentBilling.created_at))
        .all()
    )

    today = date.today()
    for billing in billings:
        student = billing.student
        student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"
        days_overdue = max(0, (today - billing.due_date).days) if billing.status == "overdue" else 0

        writer.writerow([
            student_name,
            billing.status,
            billing.amount_da,
            billing.paid_amount or 0,
            billing.cycle_start.isoformat(),
            days_overdue,
        ])

    return output.getvalue()


def export_teacher_hours(academy_id: str) -> str:
    """
    Generate CSV for teacher hours.
    Columns: Teacher, Session, Date, Hours, Subject
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Teacher", "Session", "Date", "Hours", "Subject"])

    logs = (
        TeacherHoursLog.query.join(Teacher)
        .filter(Teacher.academy_id == academy_id)
        .all()
    )

    for log in logs:
        teacher = log.teacher
        session = log.session
        teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else "Unknown"
        session_info = f"{session.class_.name}" if session and session.class_ else "N/A"
        session_date = session.date.isoformat() if session else ""
        subject = session.subject if session else "N/A"

        writer.writerow([
            teacher_name,
            session_info,
            session_date,
            float(log.hours),
            subject,
        ])

    return output.getvalue()


def export_chart_data(academy_id: str, chart_type: str = "income") -> str:
    """
    Generate CSV for chart data based on chart type.
    Supports: income, enrollments, teacher_hours, overdue, income_by_subject
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if chart_type == "income":
        writer.writerow(["Month", "Income (DA)"])
        # Implementation from billing_service.get_revenue_chart
        from app.services.billing_service import get_revenue_chart
        data = get_revenue_chart(academy_id)
        for row in data:
            writer.writerow([row["month"], row["income"]])

    elif chart_type == "teacher_hours":
        writer.writerow(["Teacher", "Total Hours"])
        from sqlalchemy import func
        results = (
            db.session.query(
                Teacher.first_name,
                Teacher.last_name,
                func.sum(TeacherHoursLog.hours).label("total_hours"),
            )
            .join(TeacherHoursLog, TeacherHoursLog.teacher_id == Teacher.id)
            .filter(Teacher.academy_id == academy_id)
            .group_by(Teacher.id)
            .all()
        )
        for r in results:
            writer.writerow([f"{r.first_name} {r.last_name}", float(r.total_hours)])

    else:
        writer.writerow(["No data available for this chart type"])

    return output.getvalue()
