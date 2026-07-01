"""
OpenCareOS - Base Repository
Apache License 2.0
"""

from typing import Generic, TypeVar, Optional, List, Type, Any
from uuid import UUID
from beanie import Document, PydanticObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.base import BaseDocument, PaginationParams, PaginatedResponse

T = TypeVar("T", bound=BaseDocument)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, document: T) -> T:
        """Create a new document."""
        await document.insert()
        return document

    async def get_by_id(self, id: UUID | PydanticObjectId | str) -> Optional[T]:
        """Get document by ID."""
        return await self.model.get(id)

    async def get_by_id_or_404(self, id: UUID | PydanticObjectId | str) -> T:
        """Get document by ID or raise NotFoundError."""
        doc = await self.get_by_id(id)
        if not doc:
            from app.core.exceptions import NotFoundError
            raise NotFoundError(self.model.__name__, str(id))
        return doc

    async def update(self, document: T) -> T:
        """Update an existing document."""
        await document.save()
        return document

    async def delete(self, id: UUID | PydanticObjectId | str, user_id: Optional[UUID | PydanticObjectId] = None) -> bool:
        """Hard delete a document."""
        doc = await self.get_by_id(id)
        if not doc:
            return False
        await doc.delete()
        return True

    async def soft_delete(self, id: UUID | PydanticObjectId | str, user_id: Optional[UUID | PydanticObjectId] = None) -> bool:
        """Soft delete a document."""
        doc = await self.get_by_id(id)
        if not doc:
            return False
        await doc.soft_delete(user_id)
        return True

    async def restore(self, id: UUID | PydanticObjectId | str) -> bool:
        """Restore a soft-deleted document."""
        doc = await self.get_by_id(id)
        if not doc:
            return False
        await doc.restore()
        return True

    async def list(
        self,
        params: PaginationParams,
        filters: Optional[dict] = None,
        sort_field: str = "created_at",
        sort_order: int = DESCENDING,
    ) -> PaginatedResponse[T]:
        """List documents with pagination and filters."""
        query = filters or {}
        query["is_deleted"] = {"$ne": True}

        total = await self.model.find(query).count()
        items = await self.model.find(query).sort(
            [(sort_field, sort_order)]
        ).skip(params.skip).limit(params.limit).to_list()

        return PaginatedResponse.create(items, total, params)

    async def find_one(self, filters: dict) -> Optional[T]:
        """Find a single document by filters."""
        filters["is_deleted"] = {"$ne": True}
        return await self.model.find_one(filters)

    async def find_many(
        self,
        filters: dict,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "created_at",
        sort_order: int = DESCENDING,
    ) -> List[T]:
        """Find multiple documents by filters."""
        filters["is_deleted"] = {"$ne": True}
        return await self.model.find(filters).sort(
            [(sort_field, sort_order)]
        ).skip(skip).limit(limit).to_list()

    async def count(self, filters: Optional[dict] = None) -> int:
        """Count documents matching filters."""
        query = filters or {}
        query["is_deleted"] = {"$ne": True}
        return await self.model.find(query).count()

    async def exists(self, filters: dict) -> bool:
        """Check if any document matches filters."""
        filters["is_deleted"] = {"$ne": True}
        return await self.model.find(filters).count() > 0