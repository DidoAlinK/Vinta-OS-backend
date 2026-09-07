"""
Vinta School OS — Configuration Environments
Dev, Test, and Production configurations for the Flask application.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Shared configuration across all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "vinta-change-this-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "vinta-jwt-change-this")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/vinta_school_dev",
    )

    # Flask-Migrate
    MIGRATION_DIR = "migrations"

    # Pagination defaults
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100

    # Phone format (+213)
    PHONE_COUNTRY_CODE = "+213"

    # Currency
    DEFAULT_CURRENCY = "DZD"

    # Timezone (Algeria)
    TIMEZONE = "Africa/Algiers"


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL queries in development


class TestingConfig(BaseConfig):
    """Test environment configuration."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/vinta_school_test",
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
