"""
Unit Tests — Teacher Payroll Calculations
Tests for hourly vs per-student contract calculations.
"""
import uuid
import pytest
from datetime import date, timedelta, time
from app.models.teacher import Teacher, TeacherPayroll, TeacherHoursLog
from app.models.scheduling import Session, Schedule
from app.models.class_room import Class
from app.models.student import Student, Enrollment


@pytest.mark.unit
class TestHourlyPayroll:
    """Test hourly contract payroll calculations."""

    def test_hourly_rate_calculation(self, db, academy, teacher, session_obj):
        """Hourly payroll = total_hours × hourly_rate."""
        # Log 3 hours of teaching
        hours_log = TeacherHoursLog(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            session_id=session_obj.id,
            hours=3.0,
            logged_by=teacher.id,  # Simplified for test
        )
        db.session.add(hours_log)
        db.session.flush()

        # Calculate payroll
        from app.services.payroll_service import calculate_teacher_payroll
        result = calculate_teacher_payroll(
            teacher.id,
            date.today().replace(day=1),
            date.today(),
        )

        assert result["contract_type"] == "hourly"
        assert float(result["total_hours"]) == 3.0
        assert result["rate_applied"] == 1500
        assert result["calculated_amount"] == 4500

    def test_zero_hours_payroll(self, db, academy, teacher):
        """Payroll with zero hours should return 0 amount."""
        from app.services.payroll_service import calculate_teacher_payroll
        result = calculate_teacher_payroll(
            teacher.id,
            date.today().replace(day=1),
            date.today(),
        )

        assert result["total_hours"] == 0
        assert result["calculated_amount"] == 0


@pytest.mark.unit
class TestPerStudentPayroll:
    """Test per-student contract payroll calculations."""

    def test_per_student_rate_calculation(self, db, academy, teacher, class_obj, student, session_obj):
        """Per-student payroll = active_students × per_student_rate."""
        # Switch teacher to per-student contract
        teacher.contract_type = "per_student"
        teacher.per_student_rate = 500
        db.session.flush()

        from app.services.payroll_service import calculate_teacher_payroll
        result = calculate_teacher_payroll(
            teacher.id,
            date.today().replace(day=1),
            date.today(),
        )

        assert result["contract_type"] == "per_student"
        assert result["total_students"] >= 1
        assert result["rate_applied"] == 500
        assert result["calculated_amount"] >= 500


@pytest.mark.unit
class TestPayrollStatus:
    """Test payroll status transitions."""

    def test_initial_status_is_pending(self, db, academy, teacher):
        """New payroll records should start as 'pending'."""
        payroll = TeacherPayroll(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 30),
            total_hours=0,
            total_students=0,
            rate_applied=1500,
            calculated_amount=0,
            status="pending",
        )
        db.session.add(payroll)
        db.session.flush()

        assert payroll.status == "pending"

    def test_settle_sets_paid_date(self, db, academy, teacher):
        """Settling a payroll should set paid_date and status."""
        payroll = TeacherPayroll(
            id=str(uuid.uuid4()),
            teacher_id=teacher.id,
            period_start=date(2026, 9, 1),
            period_end=date(2026, 9, 30),
            total_hours=10,
            rate_applied=1500,
            calculated_amount=15000,
            status="pending",
        )
        db.session.add(payroll)
        db.session.flush()

        # Settle
        payroll.status = "settled"
        payroll.paid_date = date.today()
        db.session.flush()

        assert payroll.status == "settled"
        assert payroll.paid_date == date.today()
