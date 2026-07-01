"""
OpenCareOS - Auth API Router
Apache License 2.0
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from uuid import UUID
from app.core.config.settings import get_settings
from app.core.exceptions import UnauthorizedError, ValidationError, ConflictError, open_care_exception_to_http
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserProfileResponse,
    UserUpdateRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    LogoutRequest,
    MessageResponse,
)
from app.schemas.base import APIResponse
from app.services.auth import auth_service
from app.models.user import User
from app.repositories.user import user_repository
from app.models.audit import AuditLogger, AuditAction, AuditResource

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """Get current authenticated user."""
    # Try cookie first, then header
    token_value = access_token or token
    if not token_value:
        raise UnauthorizedError("Not authenticated")

    try:
        user = await auth_service.get_current_user(token_value)
        return user
    except Exception as e:
        raise UnauthorizedError(str(e))


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise UnauthorizedError("Inactive user")
    return current_user


async def get_optional_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    token_value = access_token or token
    if not token_value:
        return None
    try:
        return await auth_service.get_current_user(token_value)
    except Exception:
        return None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str, remember_me: bool = False):
    """Set authentication cookies."""
    max_age = settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60 if remember_me else settings.JWT_EXPIRE_MINUTES * 60

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token", path="/", httponly=True, secure=not settings.DEBUG, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/", httponly=True, secure=not settings.DEBUG, samesite="lax")


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    response: Response,
    request: Request,
    login_data: LoginRequest,
):
    """User login."""
    try:
        user, access_token, refresh_token, expires_in = await auth_service.login(
            email=login_data.email,
            password=login_data.password,
            remember_me=login_data.remember_me,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        set_auth_cookies(response, access_token, refresh_token, login_data.remember_me)

        return APIResponse.success_response(
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=expires_in,
                user=UserResponse.model_validate(user),
            ),
            message="Login successful",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    response: Response,
    request: Request,
    register_data: RegisterRequest,
):
    """User registration."""
    try:
        user = await auth_service.register(register_data)

        # Auto-login after registration
        access_token, expires_in = auth_service.create_access_token(user)
        refresh_token = auth_service.create_refresh_token(user)
        user.add_refresh_token(refresh_token)
        await user.save()

        set_auth_cookies(response, access_token, refresh_token, False)

        return APIResponse.success_response(
            data=UserResponse.model_validate(user),
            message="Registration successful",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/logout", response_model=APIResponse[MessageResponse])
async def logout(
    response: Response,
    request: Request,
    logout_data: LogoutRequest = None,
    current_user: User = Depends(get_current_active_user),
):
    """User logout."""
    refresh_token = request.cookies.get("refresh_token")
    await auth_service.logout(current_user, refresh_token, logout_data.revoke_all if logout_data else False)
    clear_auth_cookies(response)

    return APIResponse.success_response(
        data=MessageResponse(message="Logged out successfully"),
        message="Logged out successfully",
    )


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    response: Response,
    request: Request,
    refresh_data: RefreshTokenRequest = None,
):
    """Refresh access token."""
    refresh_token = None
    if refresh_data and refresh_data.refresh_token:
        refresh_token = refresh_data.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise UnauthorizedError("Refresh token required")

    try:
        access_token, expires_in = await auth_service.refresh_access_token(refresh_token)
        new_refresh_token = auth_service.create_refresh_token(
            await user_repository.get_by_id(UUID((await auth_service.verify_refresh_token(refresh_token)).sub))
        )

        # Update user's refresh tokens
        user = await user_repository.get_by_id(UUID((await auth_service.verify_refresh_token(refresh_token)).sub))
        if user:
            user.remove_refresh_token(refresh_token)
            user.add_refresh_token(new_refresh_token)
            await user.save()

        set_auth_cookies(response, access_token, new_refresh_token, False)

        user_obj = await user_repository.get_by_id(UUID((await auth_service.verify_refresh_token(refresh_token)).sub))

        return APIResponse.success_response(
            data=TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=expires_in,
                user=UserResponse.model_validate(user_obj),
            ),
            message="Token refreshed",
        )
    except Exception as e:
        clear_auth_cookies(response)
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/me", response_model=APIResponse[UserProfileResponse])
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile."""
    return APIResponse.success_response(
        data=UserProfileResponse.model_validate(current_user),
    )


@router.patch("/me", response_model=APIResponse[UserProfileResponse])
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update current user profile."""
    update_dict = update_data.model_dump(exclude_unset=True)
    old_values = current_user.model_dump()

    for field, value in update_dict.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    current_user.updated_by = current_user.id
    await current_user.save()

    await AuditLogger.log_update(
        resource=AuditResource.USER,
        resource_id=current_user.id,
        resource_identifier=current_user.email,
        user_id=current_user.id,
        user_role=current_user.role.value,
        user_email=current_user.email,
        description="Profile updated",
        old_values=old_values,
        new_values=current_user.model_dump(),
    )

    return APIResponse.success_response(
        data=UserProfileResponse.model_validate(current_user),
        message="Profile updated successfully",
    )


@router.post("/change-password", response_model=APIResponse[MessageResponse])
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Change password."""
    if password_data.new_password != password_data.confirm_password:
        raise ValidationError("New passwords do not match")

    await auth_service.change_password(
        current_user,
        password_data.current_password,
        password_data.new_password,
    )

    return APIResponse.success_response(
        data=MessageResponse(message="Password changed successfully"),
        message="Password changed successfully",
    )


@router.get("/verify", response_model=APIResponse[dict])
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """Verify if token is valid."""
    return APIResponse.success_response(
        data={
            "valid": True,
            "user_id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role.value,
        },
    )