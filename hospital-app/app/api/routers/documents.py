"""
OpenCareOS - Document API Router
Apache License 2.0
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from uuid import UUID
from datetime import datetime
from app.core.exceptions import NotFoundError, ValidationError, open_care_exception_to_http
from app.schemas.document import (
    DocumentCreateRequest,
    DocumentUpdateRequest,
    DocumentResponse,
    DocumentSummaryResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    DocumentFilterParams,
)
from app.schemas.base import APIResponse, PaginationParams
from app.services.document import document_service
from app.models.user import User
from app.api.routers.auth import get_current_active_user

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=APIResponse[DocumentUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    patient_id: UUID = Form(...),
    encounter_id: Optional[UUID] = Form(None),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    category: Optional[str] = Form(None),
    is_confidential: bool = Form(False),
    access_level: str = Form("standard"),
    allowed_roles: Optional[str] = Form(None),  # Comma-separated
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a new document with file."""
    # Check permissions
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Can only upload documents for yourself")

    # Validate file
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    if file.content_type not in allowed_types:
        raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_types)}")

    # Read file content
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:  # 50MB
        raise ValidationError("File size exceeds 50MB limit")

    # Parse tags and allowed_roles
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    allowed_roles_list = [r.strip() for r in allowed_roles.split(",")] if allowed_roles else []

    # Create document request
    doc_data = DocumentCreateRequest(
        patient_id=patient_id,
        encounter_id=encounter_id,
        document_type=document_type,
        title=title,
        description=description,
        tags=tag_list,
        category=category,
        is_confidential=is_confidential,
        access_level=access_level,
        allowed_roles=allowed_roles_list,
    )

    try:
        document = await document_service.create_document(
            doc_data,
            file_content,
            file.filename,
            current_user,
        )

        return APIResponse.success_response(
            data=DocumentUploadResponse(
                document=DocumentResponse.model_validate(document),
            ),
            message="Document uploaded successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/{document_id}", response_model=APIResponse[DocumentResponse])
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Get document by ID."""
    try:
        document = await document_service.get_document(document_id)

        # Check permissions
        if current_user.is_patient:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient_by_user(current_user.id)
            if not patient or document.patient_id != patient.id:
                raise HTTPException(status_code=403, detail="Not authorized")

        return APIResponse.success_response(data=DocumentResponse.model_validate(document))
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.patch("/{document_id}", response_model=APIResponse[DocumentResponse])
async def update_document(
    document_id: UUID,
    update_data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update document metadata (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        document = await document_service.update_document(document_id, update_data, current_user)
        return APIResponse.success_response(
            data=DocumentResponse.model_validate(document),
            message="Document updated successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/{document_id}/version", response_model=APIResponse[DocumentResponse])
async def create_document_version(
    document_id: UUID,
    amendment_reason: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new version of an existing document (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate file
    file_content = await file.read()
    if len(file_content) > 50 * 1024 * 1024:
        raise ValidationError("File size exceeds 50MB limit")

    try:
        document = await document_service.create_new_version(
            document_id,
            file_content,
            file.filename,
            amendment_reason,
            current_user,
        )
        return APIResponse.success_response(
            data=DocumentResponse.model_validate(document),
            message="New document version created",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.delete("/{document_id}", response_model=APIResponse[dict])
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Delete document (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        await document_service.delete_document(document_id, current_user)
        return APIResponse.success_response(
            data={"deleted": True},
            message="Document deleted successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Download document file."""
    try:
        file_path, file_name, mime_type, file_size = await document_service.get_file_for_download(document_id)

        # Check permissions
        document = await document_service.get_document(document_id)
        if current_user.is_patient:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient_by_user(current_user.id)
            if not patient or document.patient_id != patient.id:
                raise HTTPException(status_code=403, detail="Not authorized")

        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=mime_type,
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("", response_model=APIResponse[DocumentListResponse])
async def list_documents(
    patient_id: Optional[UUID] = None,
    encounter_id: Optional[UUID] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """List documents with filters."""
    from app.models.document import DocumentType, DocumentStatus

    # Build filter params
    params = PaginationParams(page=page, size=size)
    filters = {}

    if patient_id:
        filters["patient_id"] = patient_id
    if encounter_id:
        filters["encounter_id"] = encounter_id
    if document_type:
        filters["document_type"] = DocumentType(document_type)
    if status:
        filters["status"] = DocumentStatus(status)

    # Apply permission filters
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if patient:
            filters["patient_id"] = patient.id
        else:
            filters["patient_id"] = UUID("00000000-0000-0000-0000-000000000000")

    documents = await document_service.list_documents(params=params, **filters)

    return APIResponse.success_response(
        data=DocumentListResponse(
            documents=[DocumentSummaryResponse.model_validate(d) for d in documents.items],
            total=documents.total,
            page=documents.page,
            size=documents.size,
            pages=documents.pages,
        )
    )


@router.get("/patient/{patient_id}", response_model=APIResponse[DocumentListResponse])
async def get_patient_documents(
    patient_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get all documents for a patient."""
    # Check permissions
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")

    params = PaginationParams(page=page, size=size)
    documents = await document_service.get_patient_documents(patient_id, params)

    return APIResponse.success_response(
        data=DocumentListResponse(
            documents=[DocumentSummaryResponse.model_validate(d) for d in documents.items],
            total=documents.total,
            page=documents.page,
            size=documents.size,
            pages=documents.pages,
        )
    )


@router.get("/encounter/{encounter_id}", response_model=APIResponse[DocumentListResponse])
async def get_encounter_documents(
    encounter_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get all documents for an encounter."""
    params = PaginationParams(page=page, size=size)
    documents = await document_service.get_encounter_documents(encounter_id, params)

    return APIResponse.success_response(
        data=DocumentListResponse(
            documents=[DocumentSummaryResponse.model_validate(d) for d in documents.items],
            total=documents.total,
            page=documents.page,
            size=documents.size,
            pages=documents.pages,
        )
    )