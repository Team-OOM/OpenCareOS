"""
OpenCareOS - Database Module
Apache License 2.0
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from typing import Optional, List
from app.core.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)

_settings = get_settings()

# MongoDB client instance
_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            _settings.MONGO_URI,
            maxPoolSize=_settings.MONGO_MAX_POOL_SIZE,
            minPoolSize=_settings.MONGO_MIN_POOL_SIZE,
            uuidRepresentation="standard",
        )
        logger.info("MongoDB client created")
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    global _db
    if _db is None:
        client = await get_client()
        _db = client[_settings.MONGO_DB_NAME]
        logger.info(f"Connected to database: {_settings.MONGO_DB_NAME}")
    return _db


async def init_database() -> None:
    """Initialize database connection and Beanie ODM."""
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.encounter import Encounter
    from app.models.document import Document
    from app.models.audit import AuditLog

    db = await get_database()
    await init_beanie(
        database=db,
        document_models=[
            User,
            Patient,
            Encounter,
            Document,
            AuditLog,
        ],
    )
    logger.info("Beanie ODM initialized with document models")


async def close_database() -> None:
    """Close database connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


async def get_collection(name: str):
    """Get a collection by name."""
    db = await get_database()
    return db[name]


async def create_indexes() -> None:
    """Create database indexes."""
    from app.models.user import User
    from app.models.patient import Patient
    from app.models.encounter import Encounter
    from app.models.document import Document
    from app.models.audit import AuditLog

    models = [User, Patient, Encounter, Document, AuditLog]
    for model in models:
        await model.create_indexes()
    logger.info("Database indexes created")