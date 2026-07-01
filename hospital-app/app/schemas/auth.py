"""
OpenCareOS - Authentication Schemas
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from app.models.user import UserRole, UserStatus
from app.schemas.base import BaseSchema, APIResponse, PaginatedResponse, PaginationParams


# --- Request Schemas ---

class LoginRequest(BaseSchema):
    """Login request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    remember_me: bool = Field(default=False, description="Extend token expiry")
    two_factor_code: Optional[str] = Field(default=None, min_length=6, max_length=6, description="2FA code")


class RegisterRequest(BaseSchema):
    """Registration request."""

    email: EmailStr = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$", description="Username")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$", description="Phone number")
    role: UserRole = Field(default=UserRole.PATIENT, description="User role")


class PasswordChangeRequest(BaseSchema):
    """Password change request."""

    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequest(BaseSchema):
    """Password reset request."""

    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirmRequest(BaseSchema):
    """Password reset confirmation request."""

    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)


class TwoFactorSetupRequest(BaseSchema):
    """2FA setup request."""

    enabled: bool = Field(..., description="Enable or disable 2FA")
    code: Optional[str] = Field(default=None, min_length=6, max_length=6, description="Verification code")


class RefreshTokenRequest(BaseSchema):
    """Refresh token request."""

    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseSchema):
    """Logout request."""

    revoke_all: bool = Field(default=False, description="Revoke all sessions")


# --- Response Schemas ---

class TokenResponse(BaseSchema):
    """Token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: "UserResponse" = Field(..., description="User info")


class UserResponse(BaseSchema):
    """User response."""

    id: UUID
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    avatar_url: Optional[str] = None
    email_verified: bool
    two_factor_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed properties
    is_active: bool
    is_admin: bool
    is_doctor: bool
    is_patient: bool


class UserProfileResponse(BaseSchema):
    """User profile response (extended)."""

    id: UUID
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    qualifications: List[str] = []
    email_verified: bool
    email_verified_at: Optional[datetime] = None
    two_factor_enabled: bool
    language: str
    timezone: str
    notifications_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserUpdateRequest(BaseSchema):
    """User update request."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    department: Optional[str] = None
    qualifications: Optional[List[str]] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notifications_enabled: Optional[bool] = None


class UserListResponse(BaseSchema):
    """User list response."""

    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class TwoFactorSetupResponse(BaseSchema):
    """2FA setup response."""

    secret: str
    qr_code_url: str
    backup_codes: List[str]


# --- Token Payload ---

class TokenPayload(BaseSchema):
    """JWT token payload."""

    sub: str
    email: str
    username: str
    role: UserRole
    status: UserStatus
    exp: int
    iat: int
    type: str = "access"
    jti: Optional[str] = None


# Update forward references
UserResponse.model_rebuild()