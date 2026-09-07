"""
Vinta School OS — Analytics Blueprint
/api/analytics — Dashboard stats, Revenue charts, CSV export
"""
import csv
import io
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required
from app.services import billing_service, export_service

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@tenant_required
def get_dashboard():
    """
    Dashboard overview stats.
    Returns: total students, total teachers, total classes,
             today's sessions, weekly agenda summary.
    """
    from flask import g
    from datetime import date, timedelta
    from app.models.student import Student
    from app.models.teacher import Teacher
    from app.models.class_room import Class
    from app.models.scheduling import Session

    academy_id = g.current_academy_id

    total_students = Student.query.filter_by(academy_id=academy_id).count()
    total_teachers = Teacher.query.filter_by(academy_id=academy_id).count()
    total_classes = Class.query.filter_by(academy_id=academy_id).count()

    # Today's sessions
    today = date.today()
    today_sessions = Session.query.filter(
        Session.academy_id == academy_id,
        Session.date == today,
    ).count()

    # This week's sessions count
    week_start = today - timedelta(days=today.weekday() + 1)
    week_end = week_start + timedelta(days=6)
    week_sessions = Session.query.filter(
        Session.academy_id == academy_id,
        Session.date >= week_start,
        Session.date <= week_end,
    ).count()

    # Billing stats
    billing_stats = billing_service.get_billing_stats(academy_id)

    # Monthly income
    from sqlalchemy import func
    from app.models.billing import StudentBilling
    month_start = today.replace(day=1)
    monthly_income = (
        db.session.query(func.sum(StudentBilling.amount_da))
        .join(Student)
        .filter(
            Student.academy_id == academy_id,
            StudentBilling.status == "paid",
            StudentBilling.paid_date >= month_start,
        )
        .scalar() or 0
    )

    return jsonify({
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "today_sessions": today_sessions,
        "week_sessions": week_sessions,
        "monthly_income": int(monthly_income),
        "billing": billing_stats,
    }), 200


@analytics_bp.route("/revenue-chart", methods=["GET"])
@jwt_required()
@tenant_required
def revenue_chart():
    """
    Time-series revenue data.
    Query params: months (default 6)
    """
    from flask import g
    months = request.args.get("months", 6, type=int)
    data = billing_service.get_revenue_chart(g.current_academy_id, months)
    return jsonify({"chart_data": data}), 200


@analytics_bp.route("/export/<dataset>", methods=["GET"])
@jwt_required()
@tenant_required
def export_data(dataset):
    """
    Export data as CSV.
    Supported datasets: students, billing, teacher_hours, chart_data
    Query params: chart_type (for chart_data)
    """
    from flask import g

    try:
        if dataset == "students":
            csv_data = export_service.export_student_roster(g.current_academy_id)
            filename = "student_roster.csv"
        elif dataset == "billing":
            csv_data = export_service.export_billing_history(g.current_academy_id)
            filename = "billing_history.csv"
        elif dataset == "teacher_hours":
            csv_data = export_service.export_teacher_hours(g.current_academy_id)
            filename = "teacher_hours.csv"
        elif dataset == "chart_data":
            chart_type = request.args.get("chart_type", "income")
            csv_data = export_service.export_chart_data(g.current_academy_id, chart_type)
            filename = f"chart_{chart_type}.csv"
        else:
            return jsonify({"error": f"Unknown dataset: {dataset}"}), 400

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
