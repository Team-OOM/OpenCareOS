"""
OpenCareOS - Document Model
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import Field, ConfigDict
from beanie import Document, Indexed, PydanticObjectId, Link
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.models.base import BaseDocument
from app.models.user import User
from app.models.patient import Patient


class DocumentType(str, Enum):
    """Document types."""

    LAB_REPORT = "lab_report"
    RADIOLOGY_REPORT = "radiology_report"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSULTATION_NOTE = "consultation_note"
    REFERRAL_LETTER = "referral_letter"
    INSURANCE_DOCUMENT = "insurance_document"
    CONSENT_FORM = "consent_form"
    VACCINATION_RECORD = "vaccination_record"
    MEDICAL_CERTIFICATE = "medical_certificate"
    IMAGING = "imaging"
    OTHER = "other"


class DocumentStatus(str, Enum):
    """Document status."""

    DRAFT = "draft"
    FINAL = "final"
    AMENDED = "amended"
    ARCHIVED = "archived"


class Document(BaseDocument):
    """Document model for medical records and reports."""

    # References
    patient_id: Indexed(Link[Patient])
    encounter_id: Optional[Indexed(Link)] = None
    uploaded_by_id: Indexed(Link[User])

    # Document details
    document_type: DocumentType = DocumentType.OTHER
    status: DocumentStatus = DocumentStatus.DRAFT
    title: str
    description: Optional[str] = None

    # File info
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    file_hash: Optional[str] = None  # SHA256 for integrity

    # Metadata
    tags: List[str] = []
    category: Optional[str] = None
    is_confidential: bool = False

    # Versioning
    version: int = 1
    parent_document_id: Optional[Indexed(Link)] = None
    amendment_reason: Optional[str] = None

    # Access control
    access_level: str = "standard"  # standard, restricted, confidential
    allowed_roles: List[str] = []

    # Processing
    ocr_processed: bool = False
    ocr_text: Optional[str] = None
    ai_processed: bool = False
    ai_summary: Optional[str] = None
    ai_extracted_data: dict = {}

    class Settings:
        name = "documents"
        indexes = [
            IndexModel([("patient_id", ASCENDING), ("created_at", DESCENDING)]),
            IndexModel([("encounter_id", ASCENDING)]),
            IndexModel([("document_type", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("uploaded_by_id", ASCENDING)]),
            IndexModel([("tags", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("title", "text"), ("description", "text"), ("ocr_text", "text")]),
        ]
        use_state_management = True

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.file_name.split(".")[-1].lower() if "." in self.file_name else ""

    @property
    def is_image(self) -> bool:
        """Check if document is an image."""
        return self.mime_type.startswith("image/")

    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF."""
        return self.mime_type == "application/pdf"

    @property
    def size_display(self) -> str:
        """Human readable file size."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"