"""
Vinta School OS — Application Factory
Creates and configures the Flask application with all extensions and blueprints.
"""
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, socketio


def create_app(config_name="development"):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    socketio.init_app(app, cors_allowed_origins="*")

    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Register blueprints
    _register_blueprints(app)

    # Shell context
    _register_shell_context(app)

    return app


def _register_blueprints(app):
    """Register all API blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.students import students_bp
    from app.routes.teachers import teachers_bp
    from app.routes.classes import classes_bp
    from app.routes.calendar import calendar_bp
    from app.routes.attendance import attendance_bp
    from app.routes.billing import billing_bp
    from app.routes.analytics import analytics_bp
    from app.routes.settings import settings_bp
    from app.routes.notifications import notifications_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(students_bp, url_prefix="/api/students")
    app.register_blueprint(teachers_bp, url_prefix="/api/teachers")
    app.register_blueprint(classes_bp, url_prefix="/api")
    app.register_blueprint(calendar_bp, url_prefix="/api")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    app.register_blueprint(billing_bp, url_prefix="/api/billing")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")


def _register_shell_context(app):
    """Register shell context objects."""
    from app.models import academy, user, student, teacher  # noqa: F401
    from app.models import class_room, scheduling, attendance  # noqa: F401
    from app.models import billing, audit, notification  # noqa: F401

    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db)
