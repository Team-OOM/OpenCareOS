"""
OpenCareOS - Encounter/Appointment API Router
Apache License 2.0
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime
from app.core.exceptions import NotFoundError, ValidationError, ConflictError, open_care_exception_to_http
from app.schemas.encounter import (
    EncounterCreateRequest,
    EncounterUpdateRequest,
    EncounterStatusUpdateRequest,
    EncounterResponse,
    EncounterSummaryResponse,
    EncounterListResponse,
    TodayScheduleResponse,
    AppointmentBookingResponse,
    AvailabilitySlot,
    DoctorAvailabilityResponse,
    EncounterFilterParams,
)
from app.schemas.base import APIResponse, PaginationParams
from app.services.encounter import encounter_service
from app.models.user import User
from app.api.routers.auth import get_current_active_user

router = APIRouter(prefix="/api/encounters", tags=["Encounters & Appointments"])


@router.post("", response_model=APIResponse[AppointmentBookingResponse], status_code=status.HTTP_201_CREATED)
async def create_encounter(
    encounter_data: EncounterCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new appointment/encounter."""
    # Patients can only book for themselves
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or patient.id != encounter_data.patient_id:
            raise HTTPException(status_code=403, detail="Can only book appointments for yourself")

    try:
        encounter = await encounter_service.create_encounter(encounter_data, current_user)

        # Generate confirmation code
        confirmation_code = f"APT-{str(encounter.id)[:8].upper()}"

        return APIResponse.success_response(
            data=AppointmentBookingResponse(
                encounter=EncounterResponse.model_validate(encounter),
                confirmation_code=confirmation_code,
            ),
            message="Appointment booked successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/{encounter_id}", response_model=APIResponse[EncounterResponse])
async def get_encounter(
    encounter_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Get encounter by ID."""
    try:
        encounter = await encounter_service.get_encounter(encounter_id)

        # Check permissions
        if current_user.is_patient:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient_by_user(current_user.id)
            if not patient or encounter.patient_id != patient.id:
                raise HTTPException(status_code=403, detail="Not authorized")
        elif current_user.is_doctor and encounter.doctor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        return APIResponse.success_response(data=EncounterResponse.model_validate(encounter))
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.patch("/{encounter_id}", response_model=APIResponse[EncounterResponse])
async def update_encounter(
    encounter_id: UUID,
    update_data: EncounterUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update encounter (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        encounter = await encounter_service.update_encounter(encounter_id, update_data, current_user)
        return APIResponse.success_response(
            data=EncounterResponse.model_validate(encounter),
            message="Encounter updated successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.patch("/{encounter_id}/status", response_model=APIResponse[EncounterResponse])
async def update_encounter_status(
    encounter_id: UUID,
    status_data: EncounterStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update encounter status."""
    encounter = await encounter_service.get_encounter(encounter_id)

    # Check permissions
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or encounter.patient_id != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Patients can only cancel
        if status_data.status != EncounterStatus.CANCELLED:
            raise HTTPException(status_code=403, detail="Patients can only cancel appointments")
    elif current_user.is_doctor and encounter.doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        encounter = await encounter_service.update_status(encounter_id, status_data, status_data, current_user)
        return APIResponse.success_response(
            data=EncounterResponse.model_validate(encounter),
            message=f"Status updated to {status_data.status.value}",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/{encounter_id}/check-in", response_model=APIResponse[EncounterResponse])
async def check_in_encounter(
    encounter_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Patient check-in for appointment."""
    if not current_user.is_patient:
        raise HTTPException(status_code=403, detail="Only patients can check in")

    from app.services.patient import patient_service
    patient = await patient_service.get_patient_by_user(current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    try:
        encounter = await encounter_service.check_in(encounter_id, patient)
        return APIResponse.success_response(
            data=EncounterResponse.model_validate(encounter),
            message="Checked in successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/{encounter_id}/start", response_model=APIResponse[EncounterResponse])
async def start_encounter(
    encounter_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Doctor starts consultation."""
    if not current_user.is_doctor:
        raise HTTPException(status_code=403, detail="Only doctors can start consultations")

    try:
        encounter = await encounter_service.start_encounter(encounter_id, current_user)
        return APIResponse.success_response(
            data=EncounterResponse.model_validate(encounter),
            message="Consultation started",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/{encounter_id}/complete", response_model=APIResponse[EncounterResponse])
async def complete_encounter(
    encounter_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Doctor completes consultation."""
    if not current_user.is_doctor:
        raise HTTPException(status_code=403, detail="Only doctors can complete consultations")

    try:
        encounter = await encounter_service.complete_encounter(encounter_id, current_user)
        return APIResponse.success_response(
            data=EncounterResponse.model_validate(encounter),
            message="Consultation completed",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.delete("/{encounter_id}", response_model=APIResponse[dict])
async def cancel_encounter(
    encounter_id: UUID,
    reason: str = Query(..., min_length=5),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel appointment."""
    try:
        encounter = await encounter_service.cancel_encounter(encounter_id, current_user, reason)
        return APIResponse.success_response(
            data={"cancelled": True},
            message="Appointment cancelled successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("", response_model=APIResponse[EncounterListResponse])
async def list_encounters(
    patient_id: Optional[UUID] = None,
    doctor_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    encounter_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    is_telemedicine: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """List encounters with filters."""
    # Build filter params
    filters = EncounterFilterParams(
        patient_id=patient_id,
        doctor_id=doctor_id,
        department_id=department_id,
        encounter_type=encounter_type,
        status=status,
        priority=priority,
        date_from=date_from,
        date_to=date_to,
        is_telemedicine=is_telemedicine,
        page=page,
        size=size,
    )

    # Apply permission filters
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if patient:
            filters.patient_id = patient.id
        else:
            filters.patient_id = UUID("00000000-0000-0000-0000-000000000000")  # No results
    elif current_user.is_doctor:
        filters.doctor_id = current_user.id

    encounters = await encounter_service.list_encounters(filters)

    return APIResponse.success_response(
        data=EncounterListResponse(
            encounters=[EncounterSummaryResponse.model_validate(e) for e in encounters.items],
            total=encounters.total,
            page=encounters.page,
            size=encounters.size,
            pages=encounters.pages,
        )
    )


@router.get("/upcoming/me", response_model=APIResponse[List[EncounterSummaryResponse]])
async def get_my_upcoming_appointments(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
):
    """Get upcoming appointments for current user."""
    if current_user.is_patient:
        from app.services.patient import patient_service
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient:
            return APIResponse.success_response(data=[])
        encounters = await encounter_service.get_upcoming_for_patient(patient.id, limit)
    elif current_user.is_doctor:
        encounters = await encounter_service.get_upcoming_for_doctor(current_user.id, limit)
    else:
        raise HTTPException(status_code=403, detail="Not authorized")

    return APIResponse.success_response(
        data=[EncounterSummaryResponse.model_validate(e) for e in encounters]
    )


@router.get("/today/schedule", response_model=APIResponse[TodayScheduleResponse])
async def get_today_schedule(
    current_user: User = Depends(get_current_active_user),
):
    """Get today's schedule for current doctor."""
    if not current_user.is_doctor:
        raise HTTPException(status_code=403, detail="Only doctors can access schedule")

    encounters = await encounter_service.get_today_schedule(current_user.id)
    counts = await encounter_service.repo.count_by_status_for_doctor(current_user.id)

    return APIResponse.success_response(
        data=TodayScheduleResponse(
            date=datetime.utcnow(),
            total_appointments=sum(counts.values()),
            completed=counts.get("completed", 0),
            in_progress=counts.get("in_progress", 0),
            pending=counts.get("scheduled", 0) + counts.get("confirmed", 0),
            cancelled=counts.get("cancelled", 0),
            no_show=counts.get("no_show", 0),
            encounters=[EncounterSummaryResponse.model_validate(e) for e in encounters],
        )
    )


@router.get("/availability/{doctor_id}", response_model=APIResponse[DoctorAvailabilityResponse])
async def get_doctor_availability(
    doctor_id: UUID,
    date: datetime = Query(...),
    duration_minutes: int = Query(30, ge=5, le=240),
    current_user: User = Depends(get_current_active_user),
):
    """Get doctor availability for a date."""
    slots = await encounter_service.check_availability(doctor_id, date, duration_minutes)

    # Get doctor info
    from app.repositories.user import user_repository
    doctor = await user_repository.get_by_id(doctor_id)

    availability_slots = [
        AvailabilitySlot(
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            doctor_id=doctor_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            is_available=slot["available"],
        )
        for slot in slots
    ]

    return APIResponse.success_response(
        data=DoctorAvailabilityResponse(
            doctor_id=doctor_id,
            doctor_name=doctor.full_name if doctor else "Unknown",
            date=date,
            slots=availability_slots,
        )
    )


# Import EncounterStatus for use in status update
from app.models.encounter import EncounterStatus