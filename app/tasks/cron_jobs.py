"""
Vinta School OS — Cron Jobs
Automated check-outs, overdue status checks, renewal triggers.
Runs via APScheduler on a configurable schedule.
"""
import logging
from datetime import datetime, timezone
from app.extensions import db, socketio
from app.models.academy import Academy
from app.models.scheduling import Session
from app.models.billing import StudentBilling
from app.services import attendance_service, billing_service
from app.services.scheduling_service import auto_checkout_session

logger = logging.getLogger(__name__)


def auto_checkout_expired_sessions():
    """
    Check all in-progress sessions whose end_time has passed.
    If auto_checkout_enabled in AcademySettings, auto check-out all present students.
    """
    now = datetime.now(timezone.utc)
    from app.models.academy import AcademySettings

    academies = Academy.query.all()
    total_checkout_count = 0

    for academy in academies:
        settings = AcademySettings.query.filter_by(academy_id=academy.id).first()
        if not settings or not settings.auto_checkout_enabled:
            continue

        # Find sessions that have ended but have students still checked in
        expired_sessions = Session.query.filter(
            Session.academy_id ==academy.id,
            Session.status.in_(["scheduled", "in_progress"]),
        ).all()

        for session in expired_sessions:
            session_end = datetime.combine(session.date, session.end_time)
            if now > session_end:
                count = attendance_service.auto_checkout_session(session.id, academy.id)
                total_checkout_count += count

                # Mark session as completed
                session.status = "completed"

                # Emit WebSocket event for real-time UI update
                socketio.emit("session:completed", {
                    "session_id": session.id,
                    "academy_id": academy.id,
                }, room=academy.id)

                logger.info(f"Auto checkout: session {session.id} — {count} students")

    if total_checkout_count > 0:
        db.session.commit()
        logger.info(f"Total auto checkouts across all academies: {total_checkout_count}")


def check_overdue_payments():
    """
    Check all academies for billings past their due_date.
    Marks them as 'overdue' and triggers overdue alerts.
    """
    academies = Academy.query.all()
    total_overdue_count = 0

    for academy in academies:
        count = billing_service.check_overdue_billings(academy.id)
        total_overdue_count += count

        if count > 0:
            logger.info(f"Overdue check: {count} new overdue for academy {academy.id}")

    if total_overdue_count > 0:
        db.session.commit()
        logger.info(f"Total new overdue across all academies: {total_overdue_count}")


def renew_billing_cycles():
    """
    Create new billing records for students whose cycles have ended.
    Runs daily at midnight.
    """
    academies = Academy.query.all()
    total_renewed = 0

    for academy in academies:
        count = billing_service.renew_billing_cycles(academy.id)
        total_renewed += count

        if count > 0:
            logger.info(f"Cycle renewal: {count} new cycles for academy {academy.id}")

    if total_renewed > 0:
        db.session.commit()
        logger.info(f"Total renewals across all academies: {total_renewed}")


def check_upcoming_renewals():
    """
    Notify staff about upcoming billing renewals (due in 3 days).
    """
    from datetime import date, timedelta
    from app.models.notification import Notification
    import uuid

    academies = Academy.query.all()
    reminder_date = date.today() + timedelta(days=3)

    for academy in academies:
        from app.models.academy import AcademySettings
        settings = AcademySettings.query.filter_by(academy_id=academy.id).first()
        days_before = settings.billing_reminder_days_before if settings else 3

        target_date = date.today() + timedelta(days=days_before)

        upcoming = (
            StudentBilling.query.join(StudentBilling.student)
            .filter(
                StudentBilling.status == "due",
                StudentBilling.due_date == target_date,
            )
            .all()
        )

        for billing in upcoming:
            student = billing.student
            student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

            notification = Notification(
                id=str(uuid.uuid4()),
                academy_id=academy.id,
                user_id=None,  # Broadcast
                type="payment_reminder",
                title=f"Payment due in {days_before} days",
                message=f"Payment of {billing.amount_da} DA due for {student_name}",
                detail=f"Plan: {billing.payment_plan.name if billing.payment_plan else 'N/A'}",
            )
            db.session.add(notification)

    db.session.commit()


# Job schedule configuration
CRON_JOBS = [
    {
        "id": "auto_checkout",
        "func": auto_checkout_expired_sessions,
        "trigger": "interval",
        "minutes": 5,
        "description": "Auto check-out expired sessions every 5 minutes",
    },
    {
        "id": "check_overdue",
        "func": check_overdue_payments,
        "trigger": "cron",
        "hour": 1,
        "minute": 0,
        "description": "Check overdue payments daily at 1:00 AM",
    },
    {
        "id": "renew_cycles",
        "func": renew_billing_cycles,
        "trigger": "cron",
        "hour": 0,
        "minute": 0,
        "description": "Renew billing cycles daily at midnight",
    },
    {
        "id": "upcoming_renewals",
        "func": check_upcoming_renewals,
        "trigger": "cron",
        "hour": 9,
        "minute": 0,
        "description": "Check upcoming renewals daily at 9:00 AM",
    },
]
