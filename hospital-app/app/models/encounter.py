"""
OpenCareOS - Encounter Model
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import Field, ConfigDict
from beanie import Document, Indexed, PydanticObjectId, Link
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.models.base import BaseDocument
from app.models.user import User
from app.models.patient import Patient


class EncounterType(str, Enum):
    """Type of encounter."""

    APPOINTMENT = "appointment"
    CONSULTATION = "consultation"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    TELEMEDICINE = "telemedicine"
    LAB_VISIT = "lab_visit"
    PHARMACY = "pharmacy"
    ADMISSION = "admission"
    DISCHARGE = "discharge"


class EncounterStatus(str, Enum):
    """Encounter status."""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class Priority(str, Enum):
    """Encounter priority."""

    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"
    STAT = "stat"


class Encounter(BaseDocument):
    """Encounter model for appointments and consultations."""

    # References
    patient_id: Indexed(Link[Patient])
    doctor_id: Indexed(Link[User])
    department_id: Optional[Indexed(str)] = None

    # Encounter details
    encounter_type: EncounterType = EncounterType.APPOINTMENT
    status: EncounterStatus = EncounterStatus.SCHEDULED
    priority: Priority = Priority.ROUTINE

    # Scheduling
    scheduled_at: datetime
    duration_minutes: int = 30
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Location
    location: Optional[str] = None
    room: Optional[str] = None
    is_virtual: bool = False
    virtual_meeting_url: Optional[str] = None

    # Chief complaint
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None

    # Clinical
    symptoms: List[str] = []
    diagnosis: List[str] = []
    icd10_codes: List[str] = []

    # Vitals at encounter
    vitals: dict = {}

    # Notes
    doctor_notes: Optional[str] = None
    nursing_notes: Optional[str] = None
    patient_instructions: Optional[str] = None

    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None

    # Billing
    billing_code: Optional[str] = None
    billing_amount: Optional[float] = None
    insurance_claimed: bool = False

    # Metadata
    source: str = "portal"  # portal, phone, walk_in, referral
    referral_source: Optional[str] = None

    class Settings:
        name = "encounters"
        indexes = [
            IndexModel([("patient_id", ASCENDING), ("scheduled_at", DESCENDING)]),
            IndexModel([("doctor_id", ASCENDING), ("scheduled_at", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("encounter_type", ASCENDING)]),
            IndexModel([("scheduled_at", ASCENDING)]),
            IndexModel([("department_id", ASCENDING), ("scheduled_at", DESCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
        use_state_management = True

    @property
    def is_upcoming(self) -> bool:
        """Check if encounter is upcoming."""
        return self.status in [
            EncounterStatus.SCHEDULED,
            EncounterStatus.CONFIRMED,
        ] and self.scheduled_at > datetime.utcnow()

    @property
    def is_past(self) -> bool:
        """Check if encounter is in the past."""
        return self.scheduled_at < datetime.utcnow()

    @property
    def is_today(self) -> bool:
        """Check if encounter is today."""
        today = datetime.utcnow().date()
        return self.scheduled_at.date() == today

    @property
    def duration_display(self) -> str:
        """Human readable duration."""
        if self.duration_minutes < 60:
            return f"{self.duration_minutes} min"
        hours = self.duration_minutes // 60
        mins = self.duration_minutes % 60
        if mins == 0:
            return f"{hours} hr"
        return f"{hours} hr {mins} min"

    def can_be_cancelled(self, user: User) -> bool:
        """Check if encounter can be cancelled by user."""
        if self.status in [EncounterStatus.COMPLETED, EncounterStatus.CANCELLED, EncounterStatus.NO_SHOW]:
            return False
        if user.is_patient and self.patient_id != user.id:
            return False
        if user.is_doctor and self.doctor_id != user.id:
            return False
        return True

    def cancel(self, user: User, reason: str) -> None:
        """Cancel the encounter."""
        self.status = EncounterStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.updated_by = user.id