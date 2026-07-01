"""
OpenCareOS - Base Models
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from beanie import Document, PydanticObjectId
from beanie.odm.fields import Link
from pymongo import IndexModel, ASCENDING, DESCENDING


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )


class UserStampMixin(BaseModel):
    """Mixin for created_by and updated_by user references."""

    created_by: Optional[PydanticObjectId] = None
    updated_by: Optional[PydanticObjectId] = None


class BaseDocument(Document, TimestampMixin, UserStampMixin):
    """Base document with common fields."""

    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[PydanticObjectId] = None

    class Settings:
        use_state_management = True

    async def soft_delete(self, user_id: Optional[PydanticObjectId] = None) -> None:
        """Soft delete the document."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = user_id
        await self.save()

    async def restore(self) -> None:
        """Restore a soft-deleted document."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        await self.save()


class BaseModel(BaseModel):
    """Base Pydantic model with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
        str_strip_whitespace=True,
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[Any], total: int, params: PaginationParams) -> "PaginatedResponse":
        pages = (total + params.size - 1) // params.size
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )


class APIResponse(BaseModel):
    """Standard API response."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[dict] = None

    @classmethod
    def success_response(
        cls,
        data: Any = None,
        message: str = "Success",
    ) -> "APIResponse":
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(
        cls,
        message: str = "Error",
        error: Optional[dict] = None,
    ) -> "APIResponse":
        return cls(success=False, message=message, error=error)


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = {}