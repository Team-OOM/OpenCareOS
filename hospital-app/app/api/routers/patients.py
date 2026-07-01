"""
OpenCareOS - Patient API Router
Apache License 2.0
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from uuid import UUID
from app.core.exceptions import NotFoundError, ValidationError, ConflictError, open_care_exception_to_http
from app.schemas.patient import (
    PatientCreateRequest,
    PatientUpdateRequest,
    VitalsUpdateRequest,
    PatientResponse,
    PatientSummaryResponse,
    PatientListResponse,
    PatientDashboardResponse,
)
from app.schemas.base import APIResponse, PaginationParams
from app.services.patient import patient_service
from app.models.user import User
from app.api.routers.auth import get_current_active_user, get_optional_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.post("", response_model=APIResponse[PatientResponse], status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_data: PatientCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new patient record (admin/staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        patient = await patient_service.create_patient(patient_data, current_user)
        return APIResponse.success_response(
            data=PatientResponse.model_validate(patient),
            message="Patient created successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/me", response_model=APIResponse[PatientDashboardResponse])
async def get_my_patient_profile(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """Get current patient's dashboard (for patients)."""
    if not current_user.is_patient:
        raise HTTPException(status_code=403, detail="Only patients can access this endpoint")

    patient = await patient_service.get_patient_by_user(current_user.id)
    if not patient:
        raise NotFoundError("Patient profile", "not found for current user")

    dashboard = await patient_service.get_dashboard_data(patient.id)
    return APIResponse.success_response(data=dashboard)


@router.get("/{patient_id}", response_model=APIResponse[PatientResponse])
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Get patient by ID."""
    # Check permissions
    if current_user.is_patient:
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")

    try:
        patient = await patient_service.get_patient(patient_id)
        return APIResponse.success_response(data=PatientResponse.model_validate(patient))
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/mrn/{mrn}", response_model=APIResponse[PatientResponse])
async def get_patient_by_mrn(
    mrn: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get patient by MRN."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    patient = await patient_service.get_patient_by_mrn(mrn)
    if not patient:
        raise NotFoundError("Patient", mrn)

    return APIResponse.success_response(data=PatientResponse.model_validate(patient))


@router.patch("/{patient_id}", response_model=APIResponse[PatientResponse])
async def update_patient(
    patient_id: UUID,
    update_data: PatientUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update patient record."""
    # Check permissions
    if current_user.is_patient:
        patient = await patient_service.get_patient_by_user(current_user.id)
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")

    try:
        patient = await patient_service.update_patient(patient_id, update_data, current_user)
        return APIResponse.success_response(
            data=PatientResponse.model_validate(patient),
            message="Patient updated successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.patch("/{patient_id}/vitals", response_model=APIResponse[PatientResponse])
async def update_patient_vitals(
    patient_id: UUID,
    vitals_data: VitalsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Update patient vitals."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Only staff can update vitals")

    try:
        patient = await patient_service.update_vitals(patient_id, vitals_data, current_user)
        return APIResponse.success_response(
            data=PatientResponse.model_validate(patient),
            message="Vitals updated successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.delete("/{patient_id}", response_model=APIResponse[dict])
async def delete_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
):
    """Soft delete patient (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        await patient_service.delete_patient(patient_id, current_user)
        return APIResponse.success_response(
            data={"deleted": True},
            message="Patient deleted successfully",
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("", response_model=APIResponse[PatientListResponse])
async def list_patients(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """List patients (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    params = PaginationParams(page=page, size=size)
    patients = await patient_service.list_patients(params)

    return APIResponse.success_response(
        data=PatientListResponse(
            patients=[PatientSummaryResponse.model_validate(p) for p in patients.items],
            total=patients.total,
            page=patients.page,
            size=patients.size,
            pages=patients.pages,
        )
    )


@router.get("/search", response_model=APIResponse[PatientListResponse])
async def search_patients(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Search patients (staff only)."""
    if not current_user.is_staff:
        raise HTTPException(status_code=403, detail="Not authorized")

    params = PaginationParams(page=page, size=size)
    patients = await patient_service.search_patients(q, params)

    return APIResponse.success_response(
        data=PatientListResponse(
            patients=[PatientSummaryResponse.model_validate(p) for p in patients.items],
            total=patients.total,
            page=patients.page,
            size=patients.size,
            pages=patients.pages,
        )
    )


@router.get("/doctor/{doctor_id}", response_model=APIResponse[PatientListResponse])
async def get_patients_for_doctor(
    doctor_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """Get patients assigned to a doctor."""
    if current_user.is_doctor and current_user.id != doctor_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    params = PaginationParams(page=page, size=size)
    patients = await patient_service.get_patients_for_doctor(doctor_id, params)

    return APIResponse.success_response(
        data=PatientListResponse(
            patients=[PatientSummaryResponse.model_validate(p) for p in patients.items],
            total=patients.total,
            page=patients.page,
            size=patients.size,
            pages=patients.pages,
        )
    )