"""
OpenCareOS - Authentication Service
Apache License 2.0
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID, uuid4
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config.settings import get_settings
from app.core.exceptions import UnauthorizedError, ValidationError, ConflictError
from app.models.user import User, UserRole, UserStatus
from app.repositories.user import user_repository
from app.schemas.auth import TokenPayload, LoginRequest, RegisterRequest
import secrets

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for JWT tokens and user management."""

    def __init__(self):
        self.access_token_expire = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

    def create_access_token(self, user: User, remember_me: bool = False) -> Tuple[str, int]:
        """Create JWT access token."""
        expire = datetime.utcnow() + (self.refresh_token_expire if remember_me else self.access_token_expire)
        payload = user.to_token_payload()
        payload.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid4()),
        })
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token, int((expire - datetime.utcnow()).total_seconds())

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + self.refresh_token_expire
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": "refresh",
            "jti": str(uuid4()),
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return TokenPayload(**payload)
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {str(e)}")

    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify refresh token."""
        payload = self.verify_token(token)
        if payload.type != "refresh":
            raise UnauthorizedError("Invalid token type")
        return payload

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await user_repository.get_by_email(email)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        if not user.is_active:
            raise UnauthorizedError("Account is not active")
        if user.is_locked:
            raise UnauthorizedError("Account is temporarily locked")
        return user

    async def login(
        self,
        email: str,
        password: str,
        remember_me: bool = False,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Tuple[User, str, str, int]:
        """Login user and return tokens."""
        user = await self.authenticate(email, password)
        if not user:
            # Log failed attempt
            if user:
                user.record_failed_login()
                await user.save()
            from app.models.audit import AuditLogger, AuditAction, AuditResource
            await AuditLogger.log_login(
                user_id=user.id if user else None,
                user_email=email,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="Invalid credentials",
            )
            raise UnauthorizedError("Invalid email or password")

        user.record_successful_login()
        access_token, expires_in = self.create_access_token(user, remember_me)
        refresh_token = self.create_refresh_token(user)
        user.add_refresh_token(refresh_token)
        await user.save()

        # Log successful login
        from app.models.audit import AuditLogger, AuditAction, AuditResource
        await AuditLogger.log_login(
            user_id=user.id,
            user_email=user.email,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, access_token, refresh_token, expires_in

    async def register(self, data: RegisterRequest) -> User:
        """Register new user."""
        # Check if email exists
        if await user_repository.get_by_email(data.email):
            raise ConflictError("Email already registered")

        # Check if username exists
        if await user_repository.get_by_username(data.username):
            raise ConflictError("Username already taken")

        # Verify passwords match
        if data.password != data.confirm_password:
            raise ValidationError("Passwords do not match")

        # Create user
        user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            phone=data.phone,
            role=data.role,
            status=UserStatus.PENDING_VERIFICATION,
        )
        user.set_password(data.password)
        await user.insert()

        # Log registration
        from app.models.audit import AuditLogger, AuditAction, AuditResource
        await AuditLogger.log_create(
            resource=AuditResource.USER,
            resource_id=user.id,
            resource_identifier=user.email,
            user_id=user.id,
            user_role=user.role.value,
            user_email=user.email,
            description=f"User registered: {user.email}",
            new_values={"email": user.email, "role": user.role.value},
        )

        return user

    async def logout(self, user: User, refresh_token: str = None, revoke_all: bool = False) -> None:
        """Logout user."""
        if revoke_all:
            user.revoke_all_tokens()
        elif refresh_token:
            user.remove_refresh_token(refresh_token)
        await user.save()

        from app.models.audit import AuditLogger, AuditAction, AuditResource
        await AuditLogger.log(
            action=AuditAction.LOGOUT,
            resource=AuditResource.USER,
            resource_id=user.id,
            user_id=user.id,
            user_email=user.email,
            description="User logged out",
            success=True,
        )

    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, int]:
        """Refresh access token using refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        user = await user_repository.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        # Verify refresh token is valid for this user
        if refresh_token not in user.refresh_tokens:
            raise UnauthorizedError("Invalid refresh token")

        access_token, expires_in = self.create_access_token(user)
        return access_token, expires_in

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        if not user.verify_password(current_password):
            raise ValidationError("Current password is incorrect")

        user.set_password(new_password)
        user.revoke_all_tokens()  # Invalidate all sessions
        await user.save()

        from app.models.audit import AuditLogger, AuditAction, AuditResource
        await AuditLogger.log(
            action=AuditAction.PASSWORD_CHANGE,
            resource=AuditResource.USER,
            resource_id=user.id,
            user_id=user.id,
            user_email=user.email,
            description="Password changed",
            success=True,
        )

    async def request_password_reset(self, email: str) -> Optional[str]:
        """Request password reset token."""
        user = await user_repository.get_by_email(email)
        if not user:
            return None  # Don't reveal if email exists

        # Generate reset token (in production, store in DB with expiry)
        reset_token = secrets.token_urlsafe(32)
        # TODO: Store reset token with expiry in database
        # For now, return token (in production, send via email)
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        # TODO: Verify token from database
        # For now, placeholder
        return False

    async def get_current_user(self, token: str) -> User:
        """Get current user from access token."""
        payload = self.verify_token(token)
        if payload.type != "access":
            raise UnauthorizedError("Invalid token type")

        user = await user_repository.get_by_id(UUID(payload.sub))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        return user

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(password, hashed)

    def hash_password(self, password: str) -> str:
        """Hash password."""
        return pwd_context.hash(password)


auth_service = AuthService()