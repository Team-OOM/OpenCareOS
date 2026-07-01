"""
OpenCareOS - Document Service
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
import hashlib
import aiofiles
from pathlib import Path
from app.core.config.settings import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.user import User
from app.models.patient import Patient
from app.repositories.document import document_repository
from app.repositories.patient import patient_repository
from app.schemas.document import DocumentCreateRequest, DocumentUpdateRequest
from app.models.audit import AuditLogger, AuditAction, AuditResource

settings = get_settings()


class DocumentService:
    """Document service for business logic."""

    def __init__(self):
        self.repo = document_repository
        self.patient_repo = patient_repository
        self.upload_path = settings.upload_path

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def save_file(self, file_content: bytes, file_name: str) -> tuple[str, str, int, str]:
        """Save uploaded file and return path, hash, size, mime_type."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_name)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Generate unique file name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{file_name}"
        file_path = self.upload_path / unique_name

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)

        file_size = len(file_content)
        file_hash = self._calculate_file_hash(file_path)

        return str(file_path), file_hash, file_size, mime_type

    async def create_document(
        self,
        data: DocumentCreateRequest,
        file_content: bytes,
        file_name: str,
        uploaded_by: User,
    ) -> Document:
        """Create a new document with file upload."""
        # Validate patient
        patient = await self.patient_repo.get_by_id(data.patient_id)
        if not patient:
            raise NotFoundError("Patient", str(data.patient_id))

        # Validate encounter if provided
        if data.encounter_id:
            from app.repositories.encounter import encounter_repository
            encounter = await encounter_repository.get_by_id(data.encounter_id)
            if not encounter:
                raise NotFoundError("Encounter", str(data.encounter_id))
            if encounter.patient_id != patient.id:
                raise ValidationError("Encounter does not belong to this patient")

        # Save file
        file_path, file_hash, file_size, mime_type = await self.save_file(file_content, file_name)

        # Check for duplicate file
        existing = await self.repo.find_one({"file_hash": file_hash, "is_deleted": {"$ne": True}})
        if existing:
            raise ValidationError("File already exists (duplicate content)")

        # Create document
        document = Document(
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            uploaded_by_id=uploaded_by.id,
            document_type=data.document_type,
            status=DocumentStatus.FINAL,
            title=data.title,
            description=data.description,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            tags=data.tags,
            category=data.category,
            is_confidential=data.is_confidential,
            access_level=data.access_level,
            allowed_roles=data.allowed_roles,
            created_by=uploaded_by.id,
        )
        await document.insert()

        await AuditLogger.log_create(
            resource=AuditResource.DOCUMENT,
            resource_id=document.id,
            resource_identifier=document.title,
            user_id=uploaded_by.id,
            user_role=uploaded_by.role.value,
            user_email=uploaded_by.email,
            description=f"Document uploaded: {document.title}",
            new_values={
                "title": document.title,
                "type": document.document_type.value,
                "file_name": document.file_name,
                "file_size": document.file_size,
            },
            is_phi_access=True,
        )

        return document

    async def get_document(self, document_id: UUID) -> Document:
        """Get document by ID."""
        document = await self.repo.get_by_id(document_id)
        if not document:
            raise NotFoundError("Document", str(document_id))
        return document

    async def update_document(
        self,
        document_id: UUID,
        data: DocumentUpdateRequest,
        updated_by: User,
    ) -> Document:
        """Update document metadata."""
        document = await self.get_document(document_id)
        old_values = document.model_dump()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value)

        document.updated_by = updated_by.id
        await document.save()

        new_values = document.model_dump()
        await AuditLogger.log_update(
            resource=AuditResource.DOCUMENT,
            resource_id=document.id,
            resource_identifier=document.title,
            user_id=updated_by.id,
            user_role=updated_by.role.value,
            user_email=updated_by.email,
            description=f"Document updated: {document.title}",
            old_values=old_values,
            new_values=new_values,
            is_phi_access=True,
        )

        return document

    async def create_new_version(
        self,
        document_id: UUID,
        file_content: bytes,
        file_name: str,
        amendment_reason: str,
        uploaded_by: User,
    ) -> Document:
        """Create a new version of an existing document."""
        original = await self.get_document(document_id)

        # Save new file
        file_path, file_hash, file_size, mime_type = await self.save_file(file_content, file_name)

        # Create new version document
        new_version = Document(
            patient_id=original.patient_id,
            encounter_id=original.encounter_id,
            uploaded_by_id=uploaded_by.id,
            document_type=original.document_type,
            status=DocumentStatus.FINAL,
            title=original.title,
            description=original.description,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            tags=original.tags,
            category=original.category,
            is_confidential=original.is_confidential,
            access_level=original.access_level,
            allowed_roles=original.allowed_roles,
            version=original.version + 1,
            parent_document_id=original.id,
            amendment_reason=amendment_reason,
            created_by=uploaded_by.id,
        )
        await new_version.insert()

        # Mark original as amended
        original.status = DocumentStatus.AMENDED
        original.updated_by = uploaded_by.id
        await original.save()

        await AuditLogger.log_create(
            resource=AuditResource.DOCUMENT,
            resource_id=new_version.id,
            resource_identifier=new_version.title,
            user_id=uploaded_by.id,
            user_role=uploaded_by.role.value,
            user_email=uploaded_by.email,
            description=f"Document version created: {new_version.title} (v{new_version.version})",
            new_values={
                "title": new_version.title,
                "version": new_version.version,
                "parent_id": str(original.id),
            },
            is_phi_access=True,
        )

        return new_version

    async def delete_document(self, document_id: UUID, deleted_by: User) -> bool:
        """Soft delete document."""
        document = await self.get_document(document_id)
        await document.soft_delete(deleted_by.id)

        await AuditLogger.log_delete(
            resource=AuditResource.DOCUMENT,
            resource_id=document.id,
            resource_identifier=document.title,
            user_id=deleted_by.id,
            user_role=deleted_by.role.value,
            user_email=deleted_by.email,
            description=f"Document deleted: {document.title}",
            old_values={"title": document.title},
            is_phi_access=True,
        )

        return True

    async def list_documents(
        self,
        patient_id: Optional[UUID] = None,
        encounter_id: Optional[UUID] = None,
        document_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        params=None,
    ) -> List[Document]:
        """List documents with filters."""
        filters = {"is_deleted": {"$ne": True}}

        if patient_id:
            filters["patient_id"] = patient_id
        if encounter_id:
            filters["encounter_id"] = encounter_id
        if document_type:
            filters["document_type"] = document_type
        if status:
            filters["status"] = status

        from app.models.base import PaginationParams
        if params is None:
            params = PaginationParams()

        return await self.repo.list(params, filters=filters)

    async def get_patient_documents(self, patient_id: UUID, params) -> List[Document]:
        """Get all documents for a patient."""
        return await self.repo.get_by_patient(patient_id, params)

    async def get_encounter_documents(self, encounter_id: UUID, params) -> List[Document]:
        """Get all documents for an encounter."""
        return await self.repo.get_by_encounter(encounter_id, params)

    async def search_documents(
        self,
        query: str,
        patient_id: Optional[UUID] = None,
        params=None,
    ) -> List[Document]:
        """Search documents."""
        return await self.repo.search(query, patient_id, params)

    async def get_file_for_download(self, document_id: UUID) -> tuple[Path, str, str, int]:
        """Get file path and metadata for download."""
        document = await self.get_document(document_id)
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise NotFoundError("File", document.file_name)
        return file_path, document.file_name, document.mime_type, document.file_size


document_service = DocumentService()