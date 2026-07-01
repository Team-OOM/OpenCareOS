"""
OpenCareOS - Repositories Package
Apache License 2.0
"""

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository
from app.repositories.patient import PatientRepository
from app.repositories.encounter import EncounterRepository
from app.repositories.document import DocumentRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "PatientRepository",
    "EncounterRepository",
    "DocumentRepository",
]

# Singleton instances
user_repository = UserRepository()
patient_repository = PatientRepository()
encounter_repository = EncounterRepository()
document_repository = DocumentRepository()