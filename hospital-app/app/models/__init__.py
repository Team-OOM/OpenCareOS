"""
OpenCareOS - Models Package
Apache License 2.0
"""

from app.models.base import (
    BaseDocument,
    BaseModel,
    TimestampMixin,
    UserStampMixin,
    PaginationParams,
    PaginatedResponse,
    APIResponse,
    HealthCheckResponse,
)
from app.models.user import User, UserRole, UserStatus
from app.models.patient import Patient, Gender, BloodType, MaritalStatus
from app.models.encounter import Encounter, EncounterType, EncounterStatus, Priority
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.audit import AuditLog, AuditAction, AuditResource, AuditLogger

__all__ = [
    # Base
    "BaseDocument",
    "BaseModel",
    "TimestampMixin",
    "UserStampMixin",
    "PaginationParams",
    "PaginatedResponse",
    "APIResponse",
    "HealthCheckResponse",
    # User
    "User",
    "UserRole",
    "UserStatus",
    # Patient
    "Patient",
    "Gender",
    "BloodType",
    "MaritalStatus",
    # Encounter
    "Encounter",
    "EncounterType",
    "EncounterStatus",
    "Priority",
    # Document
    "Document",
    "DocumentType",
    "DocumentStatus",
    # Audit
    "AuditLog",
    "AuditAction",
    "AuditResource",
    "AuditLogger",
]