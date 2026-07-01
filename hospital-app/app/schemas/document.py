"""
OpenCareOS - Document Schemas
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from app.models.document import DocumentType, DocumentStatus
from app.schemas.base import BaseSchema


# --- Request Schemas ---

class DocumentCreateRequest(BaseSchema):
    """Document creation request (metadata only, file upload handled separately)."""

    patient_id: UUID = Field(..., description="Patient ID")
    encounter_id: Optional[UUID] = Field(default=None, description="Associated encounter ID")
    document_type: DocumentType = DocumentType.OTHER
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = Field(default=None, max_length=100)
    is_confidential: bool = False
    access_level: str = Field(default="standard")
    allowed_roles: List[str] = Field(default_factory=list)


class DocumentUpdateRequest(BaseSchema):
    """Document update request."""

    document_type: Optional[DocumentType] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[DocumentStatus] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(default=None, max_length=100)
    is_confidential: Optional[bool] = None
    access_level: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    amendment_reason: Optional[str] = Field(default=None, max_length=500)


class DocumentUploadRequest(BaseSchema):
    """Document file upload metadata."""

    file_name: str
    file_size: int = Field(..., gt=0, le=50 * 1024 * 1024)  # Max 50MB
    mime_type: str


# --- Response Schemas ---

class DocumentResponse(BaseSchema):
    """Document response."""

    id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    uploaded_by_id: UUID
    document_type: DocumentType
    status: DocumentStatus
    title: str
    description: Optional[str] = None
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    file_hash: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None
    is_confidential: bool
    access_level: str
    allowed_roles: List[str] = []
    version: int
    parent_document_id: Optional[UUID] = None
    amendment_reason: Optional[str] = None
    ocr_processed: bool
    ocr_text: Optional[str] = None
    ai_processed: bool
    ai_summary: Optional[str] = None
    ai_extracted_data: dict = {}
    created_at: datetime
    updated_at: datetime

    # Computed
    file_extension: str
    is_image: bool
    is_pdf: bool
    size_display: str


class DocumentSummaryResponse(BaseSchema):
    """Document summary for lists."""

    id: UUID
    patient_id: UUID
    patient_name: Optional[str] = None
    document_type: DocumentType
    status: DocumentStatus
    title: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_by_name: Optional[str] = None
    created_at: datetime
    size_display: str
    is_image: bool
    is_pdf: bool


class DocumentListResponse(BaseSchema):
    """Document list response."""

    documents: List[DocumentSummaryResponse]
    total: int
    page: int
    size: int
    pages: int


class DocumentUploadResponse(BaseSchema):
    """Document upload response."""

    document: DocumentResponse
    upload_url: Optional[str] = None
    message: str = "Document uploaded successfully"


class DocumentDownloadResponse(BaseSchema):
    """Document download response."""

    file_path: str
    file_name: str
    mime_type: str
    file_size: int


# --- Search/Filter Schemas ---

class DocumentFilterParams(BaseSchema):
    """Document filter parameters."""

    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    uploaded_by_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_confidential: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None  # Full-text search on title, description, ocr_text

    # Pagination
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)