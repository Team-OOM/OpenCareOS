"""
OpenCareOS - Document Repository
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from beanie import PydanticObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.document import Document, DocumentType, DocumentStatus
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Document repository with specialized queries."""

    def __init__(self):
        super().__init__(Document)

    async def get_by_patient(self, patient_id: UUID, params) -> List[Document]:
        """Get documents for a patient."""
        filters = {"patient_id": patient_id, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters, sort_field="created_at", sort_order=DESCENDING)

    async def get_by_encounter(self, encounter_id: UUID, params) -> List[Document]:
        """Get documents for an encounter."""
        filters = {"encounter_id": encounter_id, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters, sort_field="created_at", sort_order=DESCENDING)

    async def get_by_type(self, document_type: DocumentType, params) -> List[Document]:
        """Get documents by type."""
        filters = {"document_type": document_type, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_by_status(self, status: DocumentStatus, params) -> List[Document]:
        """Get documents by status."""
        filters = {"status": status, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def search(
        self,
        query: str,
        patient_id: Optional[UUID] = None,
        params=None,
    ) -> List[Document]:
        """Full-text search on documents."""
        filters = {
            "$text": {"$search": query},
            "is_deleted": {"$ne": True},
        }
        if patient_id:
            filters["patient_id"] = patient_id

        if params:
            return await self.list(params, filters=filters)
        return await self.model.find(filters).sort([("score", {"$meta": "textScore"})]).to_list()

    async def get_recent_for_patient(self, patient_id: UUID, limit: int = 10) -> List[Document]:
        """Get recent documents for a patient."""
        filters = {"patient_id": patient_id, "is_deleted": {"$ne": True}}
        return await self.model.find(filters).sort([("created_at", DESCENDING)]).limit(limit).to_list()

    async def get_lab_reports_for_patient(self, patient_id: UUID, params) -> List[Document]:
        """Get lab reports for a patient."""
        filters = {
            "patient_id": patient_id,
            "document_type": DocumentType.LAB_REPORT,
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters, sort_field="created_at", sort_order=DESCENDING)

    async def get_prescriptions_for_patient(self, patient_id: UUID, params) -> List[Document]:
        """Get prescriptions for a patient."""
        filters = {
            "patient_id": patient_id,
            "document_type": DocumentType.PRESCRIPTION,
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters, sort_field="created_at", sort_order=DESCENDING)

    async def get_imaging_for_patient(self, patient_id: UUID, params) -> List[Document]:
        """Get imaging documents for a patient."""
        filters = {
            "patient_id": patient_id,
            "document_type": DocumentType.IMAGING,
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters, sort_field="created_at", sort_order=DESCENDING)