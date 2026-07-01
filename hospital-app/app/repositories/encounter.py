"""
OpenCareOS - Encounter Repository
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from beanie import PydanticObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.encounter import Encounter, EncounterStatus, EncounterType
from app.repositories.base import BaseRepository


class EncounterRepository(BaseRepository[Encounter]):
    """Encounter repository with specialized queries."""

    def __init__(self):
        super().__init__(Encounter)

    async def get_by_patient(self, patient_id: UUID, params) -> List[Encounter]:
        """Get encounters for a patient."""
        filters = {"patient_id": patient_id, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters, sort_field="scheduled_at", sort_order=DESCENDING)

    async def get_by_doctor(self, doctor_id: UUID, params) -> List[Encounter]:
        """Get encounters for a doctor."""
        filters = {"doctor_id": doctor_id, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters, sort_field="scheduled_at", sort_order=DESCENDING)

    async def get_upcoming_for_patient(self, patient_id: UUID, limit: int = 10) -> List[Encounter]:
        """Get upcoming encounters for a patient."""
        now = datetime.utcnow()
        filters = {
            "patient_id": patient_id,
            "status": {"$in": [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED]},
            "scheduled_at": {"$gt": now},
            "is_deleted": {"$ne": True},
        }
        return await self.model.find(filters).sort([("scheduled_at", ASCENDING)]).limit(limit).to_list()

    async def get_upcoming_for_doctor(self, doctor_id: UUID, limit: int = 10) -> List[Encounter]:
        """Get upcoming encounters for a doctor."""
        now = datetime.utcnow()
        filters = {
            "doctor_id": doctor_id,
            "status": {"$in": [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED]},
            "scheduled_at": {"$gt": now},
            "is_deleted": {"$ne": True},
        }
        return await self.model.find(filters).sort([("scheduled_at", ASCENDING)]).limit(limit).to_list()

    async def get_today_for_doctor(self, doctor_id: UUID) -> List[Encounter]:
        """Get today's encounters for a doctor."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        filters = {
            "doctor_id": doctor_id,
            "scheduled_at": {"$gte": today_start, "$lt": today_end},
            "is_deleted": {"$ne": True},
        }
        return await self.model.find(filters).sort([("scheduled_at", ASCENDING)]).to_list()

    async def get_by_status(self, status: EncounterStatus, params) -> List[Encounter]:
        """Get encounters by status."""
        filters = {"status": status, "is_deleted": {"$ne": True}}
        return await self.list(params, filters=filters)

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        doctor_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        params=None,
    ) -> List[Encounter]:
        """Get encounters in date range."""
        filters = {
            "scheduled_at": {"$gte": start_date, "$lte": end_date},
            "is_deleted": {"$ne": True},
        }
        if doctor_id:
            filters["doctor_id"] = doctor_id
        if patient_id:
            filters["patient_id"] = patient_id

        if params:
            return await self.list(params, filters=filters)
        return await self.model.find(filters).sort([("scheduled_at", ASCENDING)]).to_list()

    async def get_past_for_patient(self, patient_id: UUID, params) -> List[Encounter]:
        """Get past encounters for a patient."""
        now = datetime.utcnow()
        filters = {
            "patient_id": patient_id,
            "scheduled_at": {"$lt": now},
            "is_deleted": {"$ne": True},
        }
        return await self.list(params, filters=filters, sort_field="scheduled_at", sort_order=DESCENDING)

    async def check_doctor_availability(
        self,
        doctor_id: UUID,
        scheduled_at: datetime,
        duration_minutes: int = 30,
    ) -> bool:
        """Check if doctor is available at given time."""
        start = scheduled_at
        end = scheduled_at + timedelta(minutes=duration_minutes)

        filters = {
            "doctor_id": doctor_id,
            "status": {"$in": [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED, EncounterStatus.IN_PROGRESS]},
            "is_deleted": {"$ne": True},
            "$or": [
                {"scheduled_at": {"$lt": end, "$gte": start}},
                {"$expr": {"$lt": [{"$add": ["$scheduled_at", {"$multiply": ["$duration_minutes", 60000]}]}, start]}},
            ],
        }
        count = await self.model.find(filters).count()
        return count == 0

    async def get_doctor_schedule(
        self,
        doctor_id: UUID,
        date: datetime,
    ) -> List[Encounter]:
        """Get doctor's schedule for a specific date."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        filters = {
            "doctor_id": doctor_id,
            "scheduled_at": {"$gte": start, "$lt": end},
            "is_deleted": {"$ne": True},
        }
        return await self.model.find(filters).sort([("scheduled_at", ASCENDING)]).to_list()

    async def count_by_status_for_doctor(self, doctor_id: UUID) -> dict:
        """Count encounters by status for a doctor."""
        pipeline = [
            {"$match": {"doctor_id": doctor_id, "is_deleted": {"$ne": True}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        results = await self.model.aggregate(pipeline).to_list()
        return {r["_id"]: r["count"] for r in results}