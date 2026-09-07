"""
Vinta School OS — Scheduling Service
Recurring slot generation, drag-to-rescheduling, 5-min snapping, session CRUD.
"""
import uuid
from datetime import date, time, datetime, timedelta
from sqlalchemy import and_
from app.extensions import db
from app.models.scheduling import Schedule, Session
from app.models.class_room import Class
from app.models.teacher import Teacher
from app.models.audit import ActivityLog


# 5-minute snap grid
SNAP_MINUTES = 5


def snap_time(hour: int, minute: int) -> time:
    """Snap a time to the nearest 5-minute grid."""
    snapped_minute = (minute // SNAP_MINUTES) * SNAP_MINUTES
    if snapped_minute >= 60:
        return time(hour + 1, 0)
    return time(hour, snapped_minute)


def snap_time_obj(t: time) -> time:
    """Snap a time object to the nearest 5-minute grid."""
    return snap_time(t.hour, t.minute)


def get_week_sessions(academy_id: str, week_start: date) -> list:
    """Get all sessions for a given week."""
    week_end = week_start + timedelta(days=6)

    sessions = Session.query.filter(
        Session.academy_id == academy_id,
        Session.date >= week_start,
        Session.date <= week_end,
    ).order_by(Session.date, Session.start_time).all()

    return [_serialize_session(s) for s in sessions]


def get_day_sessions(academy_id: str, target_date: date) -> list:
    """Get all sessions for a specific day."""
    sessions = Session.query.filter(
        Session.academy_id == academy_id,
        Session.date == target_date,
    ).order_by(Session.start_time).all()

    return [_serialize_session(s) for s in sessions]


def create_session(academy_id: str, data: dict, created_by: str) -> Session:
    """Create a new session (from drag-to-create or manual form)."""
    start_time = _parse_time(data["start_time"])
    end_time = _parse_time(data["end_time"])
    target_date = date.fromisoformat(data["date"])

    # Snap to 5-minute grid
    start_time = snap_time_obj(start_time)
    end_time = snap_time_obj(end_time)

    # Denormalize from class/teacher
    class_ = db.session.get(Class, data["class_id"])
    if not class_:
        raise ValueError("Class not found")

    teacher_id = data.get("teacher_id") or class_.teacher_id
    subject = data.get("subject") or class_.subject

    session = Session(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        class_id=data["class_id"],
        schedule_id=data.get("schedule_id"),
        teacher_id=teacher_id,
        classroom_id=data.get("classroom_id"),
        date=target_date,
        start_time=start_time,
        end_time=end_time,
        subject=subject,
        status="scheduled",
    )
    db.session.add(session)

    log = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=created_by,
        entity_type="session",
        entity_id=session.id,
        action="created",
        description=f"New session scheduled — {subject or class_.name}",
    )
    db.session.add(log)
    db.session.flush()

    return session


def update_session_times(session_id: str, academy_id: str, data: dict) -> Session | None:
    """
    Update session date/times (drag-to-move or edge-resize).
    Only updates on scheduled (not yet started) sessions.
    """
    session = Session.query.filter_by(
        id=session_id, academy_id=academy_id
    ).first()
    if not session or session.status != "scheduled":
        return None

    if "date" in data:
        session.date = date.fromisoformat(data["date"])
    if "start_time" in data:
        session.start_time = snap_time_obj(_parse_time(data["start_time"]))
    if "end_time" in data:
        session.end_time = snap_time_obj(_parse_time(data["end_time"]))

    db.session.flush()
    return session


def cancel_session(session_id: str, academy_id: str) -> bool:
    """Cancel a session."""
    session = Session.query.filter_by(
        id=session_id, academy_id=academy_id
    ).first()
    if not session:
        return False

    session.status = "cancelled"
    db.session.flush()
    return True


def generate_sessions_from_schedule(schedule_id: str, weeks_ahead: int = 12) -> int:
    """
    Generate concrete Session instances from a recurring Schedule entry.
    Creates sessions for the next `weeks_ahead` weeks.
    Returns the count of sessions created.
    """
    schedule = db.session.get(Schedule, schedule_id)
    if not schedule:
        return 0

    class_ = db.session.get(Class, schedule.class_id)
    if not class_:
        return 0

    count = 0
    today = date.today()
    start_date = today

    for week in range(weeks_ahead):
        # Find the next occurrence of this day_of_week
        days_ahead = schedule.day_of_week - start_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        session_date = start_date + timedelta(days=days_ahead + (week * 7))

        # Skip if session already exists
        existing = Session.query.filter_by(
            class_id=schedule.class_id,
            schedule_id=schedule_id,
            date=session_date,
        ).first()
        if existing:
            continue

        session = Session(
            id=str(uuid.uuid4()),
            academy_id=class_.academy_id,
            class_id=schedule.class_id,
            schedule_id=schedule_id,
            teacher_id=class_.teacher_id,
            classroom_id=schedule.classroom_id,
            date=session_date,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            subject=class_.subject,
            status="scheduled",
        )
        db.session.add(session)
        count += 1

    db.session.flush()
    return count


# --- Helpers ---

def _parse_time(time_str: str) -> time:
    """Parse a time string like '08:00' or '8:30' into a time object."""
    if isinstance(time_str, time):
        return time_str
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))


def _serialize_session(session: Session) -> dict:
    """Serialize a session to a dict for API response."""
    return {
        "id": session.id,
        "class_id": session.class_id,
        "class_name": session.class_.name if session.class_ else None,
        "teacher_id": session.teacher_id,
        "teacher_name": session.teacher.full_name if session.teacher else None,
        "classroom_id": session.classroom_id,
        "date": session.date.isoformat(),
        "start_time": session.start_time.strftime("%H:%M"),
        "end_time": session.end_time.strftime("%H:%M"),
        "subject": session.subject,
        "status": session.status,
        "color": session.class_.color if session.class_ else None,
    }
