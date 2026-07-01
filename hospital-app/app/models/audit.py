"""
OpenCareOS - Audit Log Model
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import Field, ConfigDict
from beanie import Document, Indexed, PydanticObjectId, Link
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.models.base import BaseDocument


class AuditAction(str, Enum):
    """Audit action types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    EXPORT = "export"
    IMPORT = "import"
    PRINT = "print"
    SHARE = "share"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    AI_INTERACTION = "ai_interaction"
    AI_TOOL_CALL = "ai_tool_call"


class AuditResource(str, Enum):
    """Audit resource types."""

    USER = "user"
    PATIENT = "patient"
    ENCOUNTER = "encounter"
    DOCUMENT = "document"
    PRESCRIPTION = "prescription"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    REPORT = "report"
    SETTINGS = "settings"
    SYSTEM = "system"


class AuditLog(BaseDocument):
    """Audit log for tracking all system activities."""

    # Actor
    user_id: Optional[Indexed(PydanticObjectId)] = None
    user_role: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Action
    action: AuditAction
    resource: AuditResource
    resource_id: Optional[PydanticObjectId] = None
    resource_identifier: Optional[str] = None  # Human readable identifier

    # Details
    description: str
    details: Dict[str, Any] = {}
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None

    # Outcome
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Context
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None

    # Compliance
    is_phi_access: bool = False  # Protected Health Information access
    consent_id: Optional[str] = None
    legal_basis: Optional[str] = None

    class Settings:
        name = "audit_logs"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("resource", ASCENDING), ("resource_id", ASCENDING)]),
            IndexModel([("action", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("is_phi_access", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("success", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("request_id", ASCENDING)]),
            IndexModel([("correlation_id", ASCENDING)]),
        ]
        use_state_management = True
        # TTL index - keep audit logs for 7 years (HIPAA compliance)
        # 7 years = 365 * 7 * 24 * 60 * 60 = 220752000 seconds
        # We'll set this programmatically rather than in indexes


class AuditLogger:
    """Service for logging audit events."""

    @staticmethod
    async def log(
        action: AuditAction,
        resource: AuditResource,
        description: str,
        user_id: Optional[PydanticObjectId] = None,
        user_role: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_id: Optional[PydanticObjectId] = None,
        resource_identifier: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        is_phi_access: bool = False,
        consent_id: Optional[str] = None,
        legal_basis: Optional[str] = None,
    ) -> AuditLog:
        """Log an audit event."""
        audit = AuditLog(
            action=action,
            resource=resource,
            description=description,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            resource_id=resource_id,
            resource_identifier=resource_identifier,
            details=details or {},
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message,
            error_code=error_code,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id,
            endpoint=endpoint,
            method=method,
            is_phi_access=is_phi_access,
            consent_id=consent_id,
            legal_basis=legal_basis,
        )
        await audit.insert()
        return audit

    @staticmethod
    async def log_create(
        resource: AuditResource,
        resource_id: PydanticObjectId,
        resource_identifier: str,
        user_id: PydanticObjectId,
        user_role: str,
        user_email: str,
        description: str,
        new_values: Dict[str, Any],
        **kwargs,
    ) -> AuditLog:
        """Log a create action."""
        return await AuditLogger.log(
            action=AuditAction.CREATE,
            resource=resource,
            resource_id=resource_id,
            resource_identifier=resource_identifier,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            description=description,
            new_values=new_values,
            **kwargs,
        )

    @staticmethod
    async def log_update(
        resource: AuditResource,
        resource_id: PydanticObjectId,
        resource_identifier: str,
        user_id: PydanticObjectId,
        user_role: str,
        user_email: str,
        description: str,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        **kwargs,
    ) -> AuditLog:
        """Log an update action."""
        return await AuditLogger.log(
            action=AuditAction.UPDATE,
            resource=resource,
            resource_id=resource_id,
            resource_identifier=resource_identifier,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            description=description,
            old_values=old_values,
            new_values=new_values,
            **kwargs,
        )

    @staticmethod
    async def log_delete(
        resource: AuditResource,
        resource_id: PydanticObjectId,
        resource_identifier: str,
        user_id: PydanticObjectId,
        user_role: str,
        user_email: str,
        description: str,
        old_values: Dict[str, Any],
        **kwargs,
    ) -> AuditLog:
        """Log a delete action."""
        return await AuditLogger.log(
            action=AuditAction.DELETE,
            resource=resource,
            resource_id=resource_id,
            resource_identifier=resource_identifier,
            user_id=user_id,
            user_role=user_role,
            user_email=user_email,
            description=description,
            old_values=old_values,
            **kwargs,
        )

    @staticmethod
    async def log_login(
        user_id: PydanticObjectId,
        user_email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> AuditLog:
        """Log a login attempt."""
        return await AuditLogger.log(
            action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
            resource=AuditResource.USER,
            resource_id=user_id,
            resource_identifier=user_email,
            user_id=user_id,
            user_email=user_email,
            description=f"User {'logged in' if success else 'failed to log in'}",
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )

    @staticmethod
    async def log_ai_interaction(
        user_id: PydanticObjectId,
        user_email: str,
        conversation_id: str,
        message: str,
        response: str,
        tools_used: list,
        ip_address: str,
        **kwargs,
    ) -> AuditLog:
        """Log an AI interaction."""
        return await AuditLogger.log(
            action=AuditAction.AI_INTERACTION,
            resource=AuditResource.SYSTEM,
            resource_identifier=conversation_id,
            user_id=user_id,
            user_email=user_email,
            description="AI chat interaction",
            details={
                "conversation_id": conversation_id,
                "message": message[:500],  # Truncate for privacy
                "response": response[:500],
                "tools_used": tools_used,
            },
            is_phi_access=True,
            ip_address=ip_address,
            **kwargs,
        )