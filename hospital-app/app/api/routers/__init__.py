"""
OpenCareOS - API Router Package
Apache License 2.0
"""

from app.api.routers.auth import router as auth_router
from app.api.routers.patients import router as patients_router
from app.api.routers.encounters import router as encounters_router
from app.api.routers.documents import router as documents_router
from app.api.routers.ai import router as ai_router

__all__ = [
    "auth_router",
    "patients_router",
    "encounters_router",
    "documents_router",
    "ai_router",
]