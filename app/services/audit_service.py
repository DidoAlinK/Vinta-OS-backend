"""
Vinta School OS — Audit Service
Staff PIN attribution logger, activity log queries.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import desc
from app.extensions import db
from app.models.audit import ActivityLog


def log_action(
    academy_id: str,
    user_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    description: str = None,
    metadata: dict = None,
) -> ActivityLog:
    """
    Create an attributed activity log entry.
    Every action is attributed to the staff member who performed it
    via their PIN — this is the core accountability feature.
    """
    entry = ActivityLog(
        id=str(uuid.uuid4()),
        academy_id=academy_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        metadata=metadata,
    )
    db.session.add(entry)
    db.session.flush()

    return entry


def get_activity_logs(
    academy_id: str,
    limit: int = 30,
    offset: int = 0,
    entity_type: str = None,
    user_id: str = None,
) -> list:
    """
    Get activity logs for an academy, newest first.
    UI shows last 30 entries with 'load more' pagination.
    """
    query = ActivityLog.query.filter_by(academy_id=academy_id)

    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if user_id:
        query = query.filter_by(user_id=user_id)

    logs = query.order_by(desc(ActivityLog.created_at)).offset(offset).limit(limit).all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else "System",
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "description": log.description,
            "metadata": log.metadata,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            # UI display helpers
            "log_type": _map_log_type(log.entity_type, log.action),
        }
        for log in logs
    ]


def _map_log_type(entity_type: str, action: str) -> str:
    """
    Map entity_type + action to UI log type for icon/color styling:
    - payment → emerald, CreditCard icon
    - checkin → gold, UserCheck icon
    - student → violet, UserPlus icon
    - alert → red, AlertCircle icon
    """
    if action in ("payment_received",):
        return "payment"
    elif action in ("checked_in", "checked_out"):
        return "checkin"
    elif action in ("created", "enrolled") and entity_type in ("student",):
        return "student"
    elif action in ("payment_overdue", "deleted", "withdrawn"):
        return "alert"
    elif action in ("created",) and entity_type == "session":
        return "checkin"
    else:
        return "student"


def get_log_count(academy_id: str) -> int:
    """Get total activity log count for an academy."""
    return ActivityLog.query.filter_by(academy_id=academy_id).count()
