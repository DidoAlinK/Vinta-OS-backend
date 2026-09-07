"""
Vinta School OS — Billing Blueprint
/api/billing — Payment Plans, Cycles, Installments, Overdue, Revenue
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required
from app.services import billing_service

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/plans", methods=["GET"])
@jwt_required()
@tenant_required
def list_plans():
    """List all payment plans for the academy."""
    from flask import g
    plans = billing_service.list_payment_plans(g.current_academy_id)
    return jsonify({"plans": plans}), 200


@billing_bp.route("/plans", methods=["POST"])
@jwt_required()
@tenant_required
def create_plan():
    """
    Create a new payment plan.
    Body: { name, duration_days, amount_da }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("name", "duration_days", "amount_da")
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    plan = billing_service.create_payment_plan(g.current_academy_id, data)
    db.session.commit()

    return jsonify({
        "id": plan.id,
        "name": plan.name,
        "duration_days": plan.duration_days,
        "amount_da": plan.amount_da,
    }), 201


@billing_bp.route("/students", methods=["GET"])
@jwt_required()
@tenant_required
def list_student_billings():
    """
    List billing records.
    Query params: student_id, status
    """
    from flask import g
    student_id = request.args.get("student_id")
    status = request.args.get("status")

    billings = billing_service.list_student_billings(
        g.current_academy_id, student_id, status
    )
    return jsonify({"billings": billings}), 200


@billing_bp.route("/record-payment", methods=["POST"])
@jwt_required()
@tenant_required
def record_payment():
    """
    Record a payment against a billing record.
    Body: { billing_id, amount, payment_method, notes? }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("billing_id", "amount")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    result = billing_service.record_payment(
        billing_id=data["billing_id"],
        amount=data["amount"],
        payment_method=data.get("payment_method", "cash"),
        recorded_by=g.current_user.id,
        academy_id=g.current_academy_id,
        notes=data.get("notes"),
    )
    if not result:
        return jsonify({"error": "Billing record not found"}), 404

    db.session.commit()
    return jsonify(result), 200


@billing_bp.route("/stats", methods=["GET"])
@jwt_required()
@tenant_required
def get_stats():
    """Get billing stats for the donut ring cards."""
    from flask import g
    stats = billing_service.get_billing_stats(g.current_academy_id)
    return jsonify(stats), 200


@billing_bp.route("/revenue-chart", methods=["GET"])
@jwt_required()
@tenant_required
def get_revenue_chart():
    """
    Get revenue chart data.
    Query params: months (default 6)
    """
    from flask import g
    months = request.args.get("months", 6, type=int)
    chart_data = billing_service.get_revenue_chart(g.current_academy_id, months)
    return jsonify({"chart_data": chart_data}), 200


@billing_bp.route("/aging-buckets", methods=["GET"])
@jwt_required()
@tenant_required
def get_aging_buckets():
    """Get overdue accounts classified into aging buckets."""
    from flask import g
    buckets = billing_service.get_aging_buckets(g.current_academy_id)
    return jsonify(buckets), 200


@billing_bp.route("/check-overdue", methods=["POST"])
@jwt_required()
@tenant_required
def check_overdue():
    """Trigger overdue status checks. Called by cron job."""
    from flask import g
    count = billing_service.check_overdue_billings(g.current_academy_id)
    db.session.commit()
    return jsonify({"overdue_count": count}), 200


@billing_bp.route("/renew-cycles", methods=["POST"])
@jwt_required()
@tenant_required
def renew_cycles():
    """Trigger billing cycle renewals. Called by cron job."""
    from flask import g
    count = billing_service.renew_billing_cycles(g.current_academy_id)
    db.session.commit()
    return jsonify({"renewed_count": count}), 200


# ── Teacher Payroll ─────────────────────────────────────────────────

@billing_bp.route("/payroll", methods=["GET"])
@jwt_required()
@tenant_required
def list_payroll():
    """
    List payroll records.
    Query params: teacher_id
    """
    from flask import g
    from app.services import payroll_service
    teacher_id = request.args.get("teacher_id")
    payrolls = payroll_service.list_teacher_payrolls(g.current_academy_id, teacher_id)
    return jsonify({"payrolls": payrolls}), 200


@billing_bp.route("/payroll/settle/<payroll_id>", methods=["POST"])
@jwt_required()
@tenant_required
def settle_payroll(payroll_id):
    """Mark a payroll record as settled (paid)."""
    from flask import g
    from app.services import payroll_service
    success = payroll_service.settle_payroll(
        payroll_id, g.current_academy_id, g.current_user.id
    )
    if not success:
        return jsonify({"error": "Payroll record not found"}), 404

    db.session.commit()
    return jsonify({"message": "Payroll settled"}), 200
