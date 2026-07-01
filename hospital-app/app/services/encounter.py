"""
OpenCareOS - Encounter Service
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.models.encounter import Encounter, EncounterType, EncounterStatus, Priority
from app.models.user import User
from app.models.patient import Patient
from app.repositories.encounter import encounter_repository
from app.repositories.patient import patient_repository
from app.repositories.user import user_repository
from app.schemas.encounter import (
    EncounterCreateRequest,
    EncounterUpdateRequest,
    EncounterStatusUpdateRequest,
    EncounterFilterParams,
)
from app.models.audit import AuditLogger, AuditAction, AuditResource


class EncounterService:
    """Encounter service for business logic."""

    def __init__(self):
        self.repo = encounter_repository
        self.patient_repo = patient_repository
        self.user_repo = user_repository

    async def create_encounter(self, data: EncounterCreateRequest, created_by: User) -> Encounter:
        """Create a new encounter/appointment."""
        # Validate patient
        patient = await self.patient_repo.get_by_id(data.patient_id)
        if not patient:
            raise NotFoundError("Patient", str(data.patient_id))

        # Validate doctor
        doctor = await self.user_repo.get_by_id(data.doctor_id)
        if not doctor:
            raise NotFoundError("Doctor", str(data.doctor_id))
        if doctor.role.value != "doctor":
            raise ValidationError("Assigned user must be a doctor")

        # Check for scheduling conflicts
        conflicts = await self._check_scheduling_conflict(
            data.doctor_id,
            data.scheduled_at,
            data.duration_minutes,
        )
        if conflicts:
            raise ConflictError("Doctor has a conflicting appointment at this time")

        # Create encounter
        encounter = Encounter(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department_id=data.department_id,
            encounter_type=data.encounter_type,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            priority=data.priority,
            chief_complaint=data.chief_complaint,
            reason_for_visit=data.reason_for_visit,
            notes=data.notes,
            location=data.location,
            is_virtual=data.is_telemedicine,
            virtual_meeting_url=data.meeting_link,
            source="portal",
            created_by=created_by.id,
        )
        await encounter.insert()

        await AuditLogger.log_create(
            resource=AuditResource.APPOINTMENT,
            resource_id=encounter.id,
            resource_identifier=f"APT-{str(encounter.id)[:8].upper()}",
            user_id=created_by.id,
            user_role=created_by.role.value,
            user_email=created_by.email,
            description=f"Appointment created for patient {patient.mrn}",
            new_values={
                "patient_id": str(data.patient_id),
                "doctor_id": str(data.doctor_id),
                "scheduled_at": data.scheduled_at.isoformat(),
                "type": data.encounter_type.value,
            },
        )

        return encounter

    async def _check_scheduling_conflict(
        self,
        doctor_id: UUID,
        scheduled_at: datetime,
        duration_minutes: int,
        exclude_id: Optional[UUID] = None,
    ) -> List[Encounter]:
        """Check for scheduling conflicts."""
        end_time = scheduled_at + timedelta(minutes=duration_minutes)
        filters = {
            "doctor_id": doctor_id,
            "status": {"$in": [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED, EncounterStatus.IN_PROGRESS]},
            "is_deleted": {"$ne": True},
            "$or": [
                {
                    "scheduled_at": {"$lt": end_time},
                    "$expr": {
                        "$gt": [
                            {"$add": ["$scheduled_at", {"$multiply": ["$duration_minutes", 60000]}]},
                            scheduled_at,
                        ]
                    },
                }
            ],
        }
        if exclude_id:
            filters["_id"] = {"$ne": exclude_id}

        return await self.repo.find_many(filters, limit=10)

    async def get_encounter(self, encounter_id: UUID) -> Encounter:
        """Get encounter by ID."""
        encounter = await self.repo.get_by_id(encounter_id)
        if not encounter:
            raise NotFoundError("Encounter", str(encounter_id))
        return encounter

    async def update_encounter(
        self,
        encounter_id: UUID,
        data: EncounterUpdateRequest,
        updated_by: User,
    ) -> Encounter:
        """Update encounter."""
        encounter = await self.get_encounter(encounter_id)
        old_values = encounter.model_dump()

        update_data = data.model_dump(exclude_unset=True)

        # Check for scheduling conflicts if time changed
        if "scheduled_at" in update_data or "duration_minutes" in update_data:
            doctor_id = update_data.get("doctor_id", encounter.doctor_id)
            scheduled_at = update_data.get("scheduled_at", encounter.scheduled_at)
            duration = update_data.get("duration_minutes", encounter.duration_minutes)

            conflicts = await self._check_scheduling_conflict(
                doctor_id,
                scheduled_at,
                duration,
                exclude_id=encounter_id,
            )
            if conflicts:
                raise ConflictError("Doctor has a conflicting appointment at this time")

        for field, value in update_data.items():
            if hasattr(encounter, field):
                setattr(encounter, field, value)

        encounter.updated_by = updated_by.id
        await encounter.save()

        new_values = encounter.model_dump()
        await AuditLogger.log_update(
            resource=AuditResource.APPOINTMENT,
            resource_id=encounter.id,
            resource_identifier=f"APT-{str(encounter.id)[:8].upper()}",
            user_id=updated_by.id,
            user_role=updated_by.role.value,
            user_email=updated_by.email,
            description=f"Appointment updated: {encounter.id}",
            old_values=old_values,
            new_values=new_values,
        )

        return encounter

    async def update_status(
        self,
        encounter_id: UUID,
        data: EncounterStatusUpdateRequest,
        updated_by: User,
    ) -> Encounter:
        """Update encounter status."""
        encounter = await self.get_encounter(encounter_id)
        old_status = encounter.status

        # Validate status transition
        if not self._is_valid_transition(old_status, data.status):
            raise ValidationError(f"Invalid status transition from {old_status.value} to {data.status.value}")

        old_values = {"status": old_status.value}

        encounter.status = data.status
        encounter.updated_by = updated_by.id

        # Set timestamps based on status
        now = datetime.utcnow()
        if data.status == EncounterStatus.CHECKED_IN:
            encounter.checked_in_at = now
        elif data.status == EncounterStatus.IN_PROGRESS:
            encounter.started_at = now
        elif data.status == EncounterStatus.COMPLETED:
            encounter.completed_at = now
        elif data.status == EncounterStatus.CANCELLED:
            encounter.cancelled_at = now
            encounter.cancellation_reason = data.cancellation_reason

        await encounter.save()

        new_values = {"status": encounter.status.value}
        await AuditLogger.log_update(
            resource=AuditResource.APPOINTMENT,
            resource_id=encounter.id,
            resource_identifier=f"APT-{str(encounter.id)[:8].upper()}",
            user_id=updated_by.id,
            user_role=updated_by.role.value,
            user_email=updated_by.email,
            description=f"Appointment status changed: {old_status.value} -> {data.status.value}",
            old_values=old_values,
            new_values=new_values,
        )

        return encounter

    def _is_valid_transition(self, from_status: EncounterStatus, to_status: EncounterStatus) -> bool:
        """Validate status transition."""
        valid_transitions = {
            EncounterStatus.SCHEDULED: [EncounterStatus.CONFIRMED, EncounterStatus.CANCELLED, EncounterStatus.RESCHEDULED],
            EncounterStatus.CONFIRMED: [EncounterStatus.CHECKED_IN, EncounterStatus.CANCELLED, EncounterStatus.RESCHEDULED, EncounterStatus.NO_SHOW],
            EncounterStatus.CHECKED_IN: [EncounterStatus.IN_PROGRESS, EncounterStatus.CANCELLED],
            EncounterStatus.IN_PROGRESS: [EncounterStatus.COMPLETED, EncounterStatus.CANCELLED],
            EncounterStatus.COMPLETED: [],
            EncounterStatus.CANCELLED: [EncounterStatus.SCHEDULED],
            EncounterStatus.NO_SHOW: [EncounterStatus.SCHEDULED],
            EncounterStatus.RESCHEDULED: [EncounterStatus.SCHEDULED, EncounterStatus.CANCELLED],
        }
        return to_status in valid_transitions.get(from_status, [])

    async def check_in(self, encounter_id: UUID, patient: Patient, vitals: dict = None) -> Encounter:
        """Patient check-in."""
        encounter = await self.get_encounter(encounter_id)

        if encounter.patient_id != patient.id:
            raise ValidationError("Patient not authorized for this encounter")

        if encounter.status not in [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED]:
            raise ValidationError("Encounter cannot be checked in")

        encounter.status = EncounterStatus.CHECKED_IN
        encounter.checked_in_at = datetime.utcnow()

        if vitals:
            encounter.vitals = vitals

        await encounter.save()
        return encounter

    async def start_encounter(self, encounter_id: UUID, doctor: User) -> Encounter:
        """Start encounter (doctor begins consultation)."""
        encounter = await self.get_encounter(encounter_id)

        if encounter.doctor_id != doctor.id:
            raise ValidationError("Doctor not authorized for this encounter")

        if encounter.status != EncounterStatus.CHECKED_IN:
            raise ValidationError("Patient must be checked in first")

        encounter.status = EncounterStatus.IN_PROGRESS
        encounter.started_at = datetime.utcnow()
        await encounter.save()
        return encounter

    async def complete_encounter(self, encounter_id: UUID, doctor: User) -> Encounter:
        """Complete encounter."""
        encounter = await self.get_encounter(encounter_id)

        if encounter.doctor_id != doctor.id:
            raise ValidationError("Doctor not authorized for this encounter")

        if encounter.status != EncounterStatus.IN_PROGRESS:
            raise ValidationError("Encounter must be in progress to complete")

        encounter.status = EncounterStatus.COMPLETED
        encounter.completed_at = datetime.utcnow()
        await encounter.save()
        return encounter

    async def cancel_encounter(
        self,
        encounter_id: UUID,
        user: User,
        reason: str,
    ) -> Encounter:
        """Cancel encounter."""
        encounter = await self.get_encounter(encounter_id)

        # Check permissions
        if user.is_patient and encounter.patient_id != user.id:
            raise ValidationError("Not authorized to cancel this appointment")
        if user.is_doctor and encounter.doctor_id != user.id:
            raise ValidationError("Not authorized to cancel this appointment")

        if not encounter.can_be_cancelled(user):
            raise ValidationError("This appointment cannot be cancelled")

        encounter.cancel(user, reason)
        await encounter.save()
        return encounter

    async def list_encounters(self, params: EncounterFilterParams) -> List[Encounter]:
        """List encounters with filters."""
        filters = {"is_deleted": {"$ne": True}}

        if params.patient_id:
            filters["patient_id"] = params.patient_id
        if params.doctor_id:
            filters["doctor_id"] = params.doctor_id
        if params.department_id:
            filters["department_id"] = params.department_id
        if params.encounter_type:
            filters["encounter_type"] = params.encounter_type
        if params.status:
            filters["status"] = params.status
        if params.priority:
            filters["priority"] = params.priority
        if params.is_telemedicine is not None:
            filters["is_virtual"] = params.is_telemedicine

        # Date range
        if params.date_from or params.date_to:
            date_filter = {}
            if params.date_from:
                date_filter["$gte"] = params.date_from
            if params.date_to:
                date_filter["$lte"] = params.date_to
            filters["scheduled_at"] = date_filter

        from app.models.base import PaginationParams
        pagination = PaginationParams(page=params.page, size=params.size)
        return await self.repo.list(pagination, filters=filters)

    async def get_today_schedule(self, doctor_id: UUID) -> List[Encounter]:
        """Get today's schedule for a doctor."""
        return await self.repo.get_today_for_doctor(doctor_id)

    async def get_upcoming_for_patient(self, patient_id: UUID, limit: int = 10) -> List[Encounter]:
        """Get upcoming encounters for patient."""
        return await self.repo.get_upcoming_for_patient(patient_id, limit)

    async def get_upcoming_for_doctor(self, doctor_id: UUID, limit: int = 10) -> List[Encounter]:
        """Get upcoming encounters for doctor."""
        return await self.repo.get_upcoming_for_doctor(doctor_id, limit)

    async def check_availability(
        self,
        doctor_id: UUID,
        date: datetime,
        duration_minutes: int = 30,
    ) -> List[dict]:
        """Check doctor availability for a date."""
        # Get doctor's schedule for the day
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        encounters = await self.repo.find_many({
            "doctor_id": doctor_id,
            "status": {"$in": [EncounterStatus.SCHEDULED, EncounterStatus.CONFIRMED, EncounterStatus.IN_PROGRESS]},
            "scheduled_at": {"$gte": start_of_day, "$lt": end_of_day},
            "is_deleted": {"$ne": True},
        })

        # Generate available slots (simplified - 9 AM to 5 PM, 30 min slots)
        slots = []
        current = start_of_day.replace(hour=9, minute=0)
        end = start_of_day.replace(hour=17, minute=0)

        while current < end:
            slot_end = current + timedelta(minutes=duration_minutes)
            conflict = False

            for enc in encounters:
                enc_end = enc.scheduled_at + timedelta(minutes=enc.duration_minutes)
                if current < enc_end and slot_end > enc.scheduled_at:
                    conflict = True
                    break

            slots.append({
                "start_time": current,
                "end_time": slot_end,
                "available": not conflict,
            })
            current = slot_end

        return slots


encounter_service = EncounterService()