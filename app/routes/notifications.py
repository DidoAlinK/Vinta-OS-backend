"""
Vinta School OS — Notifications Blueprint
/api/notifications — Toast alerts & Broadcasts
"""
import uuid
from datetime import datetime, timezone
from flask_smorest import Blueprint
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.utils.decorators import tenant_required
from app.models.notification import Notification
from app.schemas.notifications import (
    CreateNotificationRequestSchema, NotificationListResponseSchema,
    UnreadCountResponseSchema, CreateNotificationResponseSchema,
)
from app.schemas.base import ErrorSchema, MessageSchema

notifications_bp = Blueprint("notifications", __name__, description="In-app notifications & broadcasts")


@notifications_bp.route("", methods=["GET"])
@jwt_required()
@tenant_required
def list_notifications():
    """
    List notifications for the current user.
    Returns user-specific + broadcast notifications.
    Query params: unread_only (bool)
    """
    from flask import g

    user_id = g.current_user.id
    academy_id = g.current_academy_id
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    query = Notification.query.filter(
        Notification.academy_id == academy_id,
        (Notification.user_id == user_id) | (Notification.user_id.is_(None))
    )

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()

    return jsonify({
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "detail": n.detail,
                "actions": n.actions,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]
    }), 200


@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required()
@tenant_required
def get_unread_count():
    """Get the count of unread notifications."""
    from flask import g

    count = Notification.query.filter(
        Notification.academy_id == g.current_academy_id,
        (Notification.user_id == g.current_user.id) | (Notification.user_id.is_(None)),
        Notification.is_read == False,
    ).count()

    return jsonify({"unread_count": count}), 200


@notifications_bp.route("/<notification_id>/read", methods=["POST"])
@jwt_required()
@tenant_required
def mark_read(notification_id):
    """Mark a single notification as read."""
    from flask import g

    notification = Notification.query.filter_by(
        id=notification_id,
        academy_id=g.current_academy_id,
    ).first()

    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    notification.is_read = True
    db.session.commit()

    return jsonify({"message": "Notification marked as read"}), 200


@notifications_bp.route("/read-all", methods=["POST"])
@jwt_required()
@tenant_required
def mark_all_read():
    """Mark all notifications as read for the current user."""
    from flask import g

    user_id = g.current_user.id
    academy_id = g.current_academy_id

    notifications = Notification.query.filter(
        Notification.academy_id == academy_id,
        (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
        Notification.is_read == False,
    ).all()

    for n in notifications:
        n.is_read = True

    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200


@notifications_bp.route("", methods=["POST"])
@jwt_required()
@tenant_required
def create_notification():
    """
    Create a notification (broadcast or targeted).
    Body: { type, title, message, detail?, user_id?, actions? }
    """
    from flask import g
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    required = ("type", "title", "message")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    notification = Notification(
        id=str(uuid.uuid4()),
        academy_id=g.current_academy_id,
        user_id=data.get("user_id"),  # None = broadcast
        type=data["type"],
        title=data["title"],
        message=data["message"],
        detail=data.get("detail"),
        actions=data.get("actions"),
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
    }), 201
