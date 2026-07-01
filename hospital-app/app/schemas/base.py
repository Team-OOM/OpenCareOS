"""
OpenCareOS - Base Schemas
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat() if v else None},
        str_strip_whitespace=True,
        from_attributes=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UserStampSchema(BaseSchema):
    """Schema with user stamp fields."""

    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: UUID


class PaginationParams(BaseSchema):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "PaginatedResponse[T]":
        pages = (total + params.size - 1) // params.size
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )


class APIResponse(BaseSchema, Generic[T]):
    """Standard API response."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[dict] = None

    @classmethod
    def success_response(
        cls,
        data: T = None,
        message: str = "Success",
    ) -> "APIResponse[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_response(
        cls,
        message: str = "Error",
        error: Optional[dict] = None,
    ) -> "APIResponse[T]":
        return cls(success=False, message=message, error=error)


class ErrorDetail(BaseSchema):
    """Error detail."""

    code: str
    message: str
    details: Optional[dict] = None
    field: Optional[str] = None


class ErrorResponse(BaseSchema):
    """Error response."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] = []


class HealthCheckResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = {}


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str