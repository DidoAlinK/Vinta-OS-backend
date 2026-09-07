"""
Vinta School OS — Application Factory
Creates and configures the Flask application with all extensions and blueprints.
"""
from flask import Flask
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, socketio, api


def create_app(config_name="development"):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # API Documentation config
    app.config["API_TITLE"] = "Vinta School OS API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.1.0"
    app.config["OPENAPI_URL_PREFIX"] = "/api/docs"
    app.config["OPENAPI_JSON_PATH"] = "/openapi.json"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "/"
    app.config["OPENAPI_SWAGGER_UI_VERSION"] = "5.18.2"

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    socketio.init_app(app, cors_allowed_origins="*")
    api.init_app(app)

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

    # Register with smorest api for documentation
    api.register_blueprint(auth_bp, url_prefix="/api/auth", name="Auth")
    api.register_blueprint(students_bp, url_prefix="/api/students", name="Students")
    api.register_blueprint(teachers_bp, url_prefix="/api/teachers", name="Teachers")
    api.register_blueprint(classes_bp, url_prefix="/api", name="Classes")
    api.register_blueprint(calendar_bp, url_prefix="/api", name="Calendar")
    api.register_blueprint(attendance_bp, url_prefix="/api/attendance", name="Attendance")
    api.register_blueprint(billing_bp, url_prefix="/api/billing", name="Billing")
    api.register_blueprint(analytics_bp, url_prefix="/api/analytics", name="Analytics")
    api.register_blueprint(settings_bp, url_prefix="/api/settings", name="Settings")
    api.register_blueprint(notifications_bp, url_prefix="/api/notifications", name="Notifications")


def _register_shell_context(app):
    """Register shell context objects."""
    from app.models import academy, user, student, teacher  # noqa: F401
    from app.models import class_room, scheduling, attendance  # noqa: F401
    from app.models import billing, audit, notification  # noqa: F401

    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db)
