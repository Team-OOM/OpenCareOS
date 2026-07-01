"""
OpenCareOS - Patient Repository
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from beanie import PydanticObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    """Patient repository with specialized queries."""

    def __init__(self):
        super().__init__(Patient)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Patient]:
        """Get patient by linked user ID."""
        return await self.model.find_one({"user_id": user_id, "is_deleted": {"$ne": True}})

    async def get_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Get patient by MRN."""
        return await self.model.find_one({"mrn": mrn, "is_deleted": {"$ne": True}})

    async def get_by_external_id(self, external_id: str) -> Optional[Patient]:
        """Get patient by external ID."""
        return await self.model.find_one({"external_id": external_id, "is_deleted": {"$ne": True}})

    async def get_by_doctor(self, doctor_id: UUID, params) -> List[Patient]:
        """Get patients assigned to a doctor."""
        filters = {"primary_doctor_id": doctor_id, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def search(self, query: str, params) -> List[Patient]:
        """Search patients by name, MRN, email, or phone."""
        filters = {
            "$or": [
                {"mrn": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"phone": {"$regex": query, "$options": "i"}},
            ],
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters)

    async def get_by_blood_type(self, blood_type: str, params) -> List[Patient]:
        """Get patients by blood type."""
        filters = {"blood_type": blood_type, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_minors(self, params) -> List[Patient]:
        """Get minor patients (under 18)."""
        # This requires age calculation, so we'll need to fetch and filter
        # For now, return patients with date_of_birth indicating minor
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=18*365)
        filters = {"date_of_birth": {"$gt": cutoff_date}, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_with_upcoming_appointments(self, params) -> List[Patient]:
        """Get patients who have upcoming appointments."""
        # This would require a lookup/join with encounters
        # For now, we'll return patients and let service layer handle joins
        filters = {"is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def mrn_exists(self, mrn: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if MRN exists."""
        query = {"mrn": mrn, "is_deleted": {"$ne": True}}
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}
        return await self.exists(query)

    async def external_id_exists(self, external_id: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if external ID exists."""
        query = {"external_id": external_id, "is_deleted": {"$ne": True}}
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}
        return await self.exists(query)

    async def update_vitals(self, patient_id: UUID, vitals: dict) -> Optional[Patient]:
        """Update patient vitals and recalculate BMI."""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return None

        for key, value in vitals.items():
            if hasattr(patient, key):
                setattr(patient, key, value)

        patient.update_bmi()
        await patient.save()
        return patient

    async def get_patients_for_doctor_dashboard(self, doctor_id: UUID, params) -> List[Patient]:
        """Get patients for doctor's dashboard (with upcoming appointments)."""
        filters = {
            "$or": [
                {"primary_doctor_id": doctor_id},
                {"assigned_nurse_id": doctor_id},
            ],
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters)