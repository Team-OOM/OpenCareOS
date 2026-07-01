"""
OpenCareOS - User Model
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import Field, EmailStr, ConfigDict
from beanie import Document, Indexed, PydanticObjectId
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from passlib.context import CryptContext
from app.models.base import BaseDocument


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    PATIENT = "patient"
    ADMIN_STAFF = "admin_staff"


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(BaseDocument):
    """User model with authentication and authorization."""

    email: Indexed(EmailStr, unique=True)
    username: Indexed(str, unique=True)
    hashed_password: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.PATIENT
    status: UserStatus = UserStatus.PENDING_VERIFICATION

    # Profile
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None

    # Professional info (for doctors/staff)
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    qualifications: List[str] = []

    # Authentication
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    # 2FA
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    backup_codes: List[str] = []

    # Sessions
    refresh_tokens: List[str] = []

    # Preferences
    language: str = "en"
    timezone: str = "UTC"
    notifications_enabled: bool = True

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("role", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("email_verified", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("full_name", TEXT), ("email", TEXT), ("username", TEXT)]),
        ]
        use_state_management = True

    # Password methods
    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return pwd_context.verify(password, self.hashed_password)

    def set_password(self, password: str) -> None:
        """Hash and set password."""
        self.hashed_password = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    # Role checks
    @property
    def is_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    @property
    def is_doctor(self) -> bool:
        return self.role == UserRole.DOCTOR

    @property
    def is_nurse(self) -> bool:
        return self.role == UserRole.NURSE

    @property
    def is_patient(self) -> bool:
        return self.role == UserRole.PATIENT

    @property
    def is_staff(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.DOCTOR,
            UserRole.NURSE,
            UserRole.ADMIN_STAFF,
        ]

    @property
    def can_prescribe(self) -> bool:
        return self.role in [UserRole.DOCTOR, UserRole.SUPER_ADMIN, UserRole.ADMIN]

    @property
    def can_access_all_patients(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DOCTOR]

    # Status checks
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_deleted

    @property
    def is_locked(self) -> bool:
        if self.locked_until:
            return datetime.utcnow() < self.locked_until
        return False

    def record_failed_login(self) -> None:
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def record_successful_login(self) -> None:
        """Record a successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()

    # Token management
    def add_refresh_token(self, token: str) -> None:
        """Add a refresh token."""
        if token not in self.refresh_tokens:
            self.refresh_tokens.append(token)
            # Keep only last 5 tokens
            if len(self.refresh_tokens) > 5:
                self.refresh_tokens = self.refresh_tokens[-5:]

    def remove_refresh_token(self, token: str) -> None:
        """Remove a refresh token."""
        if token in self.refresh_tokens:
            self.refresh_tokens.remove(token)

    def revoke_all_tokens(self) -> None:
        """Revoke all refresh tokens."""
        self.refresh_tokens = []

    def to_token_payload(self) -> dict:
        """Convert to JWT token payload."""
        return {
            "sub": str(self.id),
            "email": self.email,
            "username": self.username,
            "role": self.role.value,
            "status": self.status.value,
        }