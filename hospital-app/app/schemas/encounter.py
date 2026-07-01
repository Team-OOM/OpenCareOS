"""
OpenCareOS - Encounter/Appointment Schemas
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from app.models.encounter import EncounterType, EncounterStatus, Priority
from app.schemas.base import BaseSchema


# --- Request Schemas ---

class EncounterCreateRequest(BaseSchema):
    """Encounter/appointment creation request."""

    patient_id: UUID = Field(..., description="Patient ID")
    doctor_id: UUID = Field(..., description="Doctor ID")
    department_id: Optional[UUID] = Field(default=None, description="Department ID")
    encounter_type: EncounterType = EncounterType.CONSULTATION
    scheduled_at: datetime = Field(..., description="Scheduled date/time")
    duration_minutes: int = Field(default=30, ge=5, le=240, description="Duration in minutes")
    priority: Priority = Priority.ROUTINE
    chief_complaint: Optional[str] = Field(default=None, max_length=500)
    reason_for_visit: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=200)
    is_telemedicine: bool = False
    meeting_link: Optional[str] = None


class EncounterUpdateRequest(BaseSchema):
    """Encounter update request."""

    doctor_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    encounter_type: Optional[EncounterType] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=240)
    priority: Optional[Priority] = None
    status: Optional[EncounterStatus] = None
    chief_complaint: Optional[str] = Field(default=None, max_length=500)
    reason_for_visit: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    location: Optional[str] = Field(default=None, max_length=200)
    is_telemedicine: Optional[bool] = None
    meeting_link: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None


class EncounterStatusUpdateRequest(BaseSchema):
    """Encounter status update request."""

    status: EncounterStatus = Field(..., description="New status")
    cancellation_reason: Optional[str] = Field(default=None, max_length=500)


class EncounterCheckInRequest(BaseSchema):
    """Patient check-in request."""

    vitals: Optional[dict] = None
    symptoms: Optional[List[str]] = None


# --- Response Schemas ---

class EncounterResponse(BaseSchema):
    """Encounter response."""

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    department_id: Optional[UUID] = None
    encounter_type: EncounterType
    status: EncounterStatus
    priority: Priority
    scheduled_at: datetime
    duration_minutes: int
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None
    is_telemedicine: bool
    meeting_link: Optional[str] = None

    # Timestamps
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # References
    consultation_id: Optional[UUID] = None
    prescription_id: Optional[UUID] = None

    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    # Computed
    is_upcoming: bool
    is_past: bool
    is_today: bool
    wait_time_minutes: Optional[int] = None


class EncounterSummaryResponse(BaseSchema):
    """Encounter summary for lists."""

    id: UUID
    patient_id: UUID
    patient_name: str
    patient_mrn: str
    doctor_id: UUID
    doctor_name: str
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    encounter_type: EncounterType
    status: EncounterStatus
    priority: Priority
    scheduled_at: datetime
    duration_minutes: int
    chief_complaint: Optional[str] = None
    is_telemedicine: bool
    is_upcoming: bool
    is_today: bool


class EncounterListResponse(BaseSchema):
    """Encounter list response."""

    encounters: List[EncounterSummaryResponse]
    total: int
    page: int
    size: int
    pages: int


class TodayScheduleResponse(BaseSchema):
    """Doctor's today schedule response."""

    date: datetime
    total_appointments: int
    completed: int
    in_progress: int
    pending: int
    cancelled: int
    no_show: int
    encounters: List[EncounterSummaryResponse]


class AppointmentBookingResponse(BaseSchema):
    """Appointment booking response."""

    encounter: EncounterResponse
    message: str = "Appointment booked successfully"
    confirmation_code: str


class AvailabilitySlot(BaseSchema):
    """Available time slot."""

    start_time: datetime
    end_time: datetime
    doctor_id: UUID
    doctor_name: str
    is_available: bool = True


class DoctorAvailabilityResponse(BaseSchema):
    """Doctor availability response."""

    doctor_id: UUID
    doctor_name: str
    date: datetime
    slots: List[AvailabilitySlot]


# --- Search/Filter Schemas ---

class EncounterFilterParams(BaseSchema):
    """Encounter filter parameters."""

    patient_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    encounter_type: Optional[EncounterType] = None
    status: Optional[EncounterStatus] = None
    priority: Optional[Priority] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_telemedicine: Optional[bool] = None

    # Pagination
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)