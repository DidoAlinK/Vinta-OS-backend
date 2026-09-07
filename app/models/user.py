"""
Vinta School OS — User Model
User (Owner/Staff) with PIN hashing, role management, and profile pictures.
"""
import uuid
import bcrypt
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Enum as SAEnum, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class User(db.Model):
    """Every person who logs into the system. Owner or Staff."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    academy_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("academies.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    role: Mapped[str] = mapped_column(
        SAEnum("owner", "staff", name="user_role_enum"), nullable=False, default="staff"
    )
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), comment="Owner password for login")
    picture: Mapped[dict | None] = mapped_column(
        JSON, comment="{ type: 'preset', colors: [hex1, hex2] } or { type: 'upload', dataUrl: '...' }"
    )
    avatar_color_1: Mapped[str | None] = mapped_column(
        String(7), comment="Legacy gradient start color"
    )
    avatar_color_2: Mapped[str | None] = mapped_column(
        String(7), comment="Legacy gradient end color"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    academy = relationship("Academy", back_populates="users")
    activity_logs = relationship("ActivityLog", back_populates="user", lazy="dynamic")

    # --- PIN Methods ---

    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a 4-digit PIN using bcrypt."""
        return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_pin(self, pin: str) -> bool:
        """Verify a PIN against the stored hash."""
        return bcrypt.checkpw(pin.encode("utf-8"), self.pin_hash.encode("utf-8"))

    def set_pin(self, pin: str):
        """Set a new PIN hash."""
        self.pin_hash = self.hash_pin(pin)

    # --- Password Methods (Owner only) ---

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))

    def set_password(self, password: str):
        """Set a new password hash (owner only)."""
        self.password_hash = self.hash_password(password)

    @property
    def is_owner(self) -> bool:
        return self.role == "owner"

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"
