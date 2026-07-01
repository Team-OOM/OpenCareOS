"""
OpenCareOS - Patient Service
Apache License 2.0
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.models.patient import Patient, Gender, BloodType, MaritalStatus
from app.models.user import User
from app.repositories.patient import patient_repository
from app.repositories.user import user_repository
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest, VitalsUpdateRequest
from app.models.audit import AuditLogger, AuditAction, AuditResource


class PatientService:
    """Patient service for business logic."""

    def __init__(self):
        self.repo = patient_repository
        self.user_repo = user_repository

    async def create_patient(self, data: PatientCreateRequest, created_by: User) -> Patient:
        """Create a new patient record."""
        # Check if user exists and is a patient
        user = await self.user_repo.get_by_id(data.user_id)
        if not user:
            raise NotFoundError("User", str(data.user_id))
        if user.role.value != "patient":
            raise ValidationError("User must have patient role")

        # Check if patient already exists for this user
        existing = await self.repo.get_by_user_id(data.user_id)
        if existing:
            raise ConflictError("Patient record already exists for this user")

        # Check MRN uniqueness
        if await self.repo.mrn_exists(data.mrn):
            raise ConflictError("MRN already exists")

        # Check external ID uniqueness
        if data.external_id and await self.repo.external_id_exists(data.external_id):
            raise ConflictError("External ID already exists")

        # Create patient
        patient = Patient(
            user_id=data.user_id,
            mrn=data.mrn,
            external_id=data.external_id,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_type=data.blood_type,
            marital_status=data.marital_status,
            phone=data.phone,
            email=data.email,
            address=data.address,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_relationship=data.emergency_contact_relationship,
            emergency_contact_phone=data.emergency_contact_phone,
            insurance_provider=data.insurance_provider,
            insurance_policy_number=data.insurance_policy_number,
            insurance_group_number=data.insurance_group_number,
            insurance_expiry=data.insurance_expiry,
            allergies=data.allergies,
            chronic_conditions=data.chronic_conditions,
            current_medications=data.current_medications,
            past_surgeries=data.past_surgeries,
            family_history=data.family_history,
            smoking_status=data.smoking_status,
            alcohol_consumption=data.alcohol_consumption,
            exercise_frequency=data.exercise_frequency,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            blood_pressure=data.blood_pressure,
            heart_rate=data.heart_rate,
            temperature_c=data.temperature_c,
            oxygen_saturation=data.oxygen_saturation,
            consent_given=data.consent_given,
            consent_date=datetime.utcnow() if data.consent_given else None,
            consent_version=data.consent_version,
            primary_doctor_id=data.primary_doctor_id,
            assigned_nurse_id=data.assigned_nurse_id,
            preferred_language=data.preferred_language,
            preferred_contact_method=data.preferred_contact_method,
            notification_preferences=data.notification_preferences,
            created_by=created_by.id,
        )
        patient.update_bmi()
        await patient.insert()

        await AuditLogger.log_create(
            resource=AuditResource.PATIENT,
            resource_id=patient.id,
            resource_identifier=patient.mrn,
            user_id=created_by.id,
            user_role=created_by.role.value,
            user_email=created_by.email,
            description=f"Patient created: {patient.mrn}",
            new_values={"mrn": patient.mrn, "user_id": str(patient.user_id)},
        )

        return patient

    async def get_patient(self, patient_id: UUID) -> Patient:
        """Get patient by ID."""
        patient = await self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient", str(patient_id))
        return patient

    async def get_patient_by_user(self, user_id: UUID) -> Optional[Patient]:
        """Get patient by user ID."""
        return await self.repo.get_by_user_id(user_id)

    async def get_patient_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Get patient by MRN."""
        return await self.repo.get_by_mrn(mrn)

    async def update_patient(
        self,
        patient_id: UUID,
        data: PatientUpdateRequest,
        updated_by: User,
    ) -> Patient:
        """Update patient record."""
        patient = await self.get_patient(patient_id)
        old_values = patient.model_dump()

        # Check MRN uniqueness if changing
        if data.mrn and data.mrn != patient.mrn:
            if await self.repo.mrn_exists(data.mrn, exclude_id=patient_id):
                raise ConflictError("MRN already exists")
            patient.mrn = data.mrn

        # Check external ID uniqueness if changing
        if data.external_id and data.external_id != patient.external_id:
            if await self.repo.external_id_exists(data.external_id, exclude_id=patient_id):
                raise ConflictError("External ID already exists")
            patient.external_id = data.external_id

        # Update fields
        update_data = data.model_dump(exclude_unset=True, exclude={"mrn", "external_id"})
        for field, value in update_data.items():
            if hasattr(patient, field):
                setattr(patient, field, value)

        # Handle consent date
        if data.consent_given and not patient.consent_given:
            patient.consent_date = datetime.utcnow()

        patient.update_bmi()
        patient.updated_by = updated_by.id
        await patient.save()

        new_values = patient.model_dump()
        await AuditLogger.log_update(
            resource=AuditResource.PATIENT,
            resource_id=patient.id,
            resource_identifier=patient.mrn,
            user_id=updated_by.id,
            user_role=updated_by.role.value,
            user_email=updated_by.email,
            description=f"Patient updated: {patient.mrn}",
            old_values=old_values,
            new_values=new_values,
        )

        return patient

    async def update_vitals(
        self,
        patient_id: UUID,
        data: VitalsUpdateRequest,
        updated_by: User,
    ) -> Patient:
        """Update patient vitals."""
        patient = await self.get_patient(patient_id)
        old_values = {"vitals": {
            "height_cm": patient.height_cm,
            "weight_kg": patient.weight_kg,
            "bmi": patient.bmi,
            "blood_pressure": patient.blood_pressure,
            "heart_rate": patient.heart_rate,
            "temperature_c": patient.temperature_c,
            "oxygen_saturation": patient.oxygen_saturation,
        }}

        vitals_data = data.model_dump(exclude_unset=True)
        for field, value in vitals_data.items():
            setattr(patient, field, value)

        patient.update_bmi()
        patient.updated_by = updated_by.id
        await patient.save()

        new_values = {"vitals": {
            "height_cm": patient.height_cm,
            "weight_kg": patient.weight_kg,
            "bmi": patient.bmi,
            "blood_pressure": patient.blood_pressure,
            "heart_rate": patient.heart_rate,
            "temperature_c": patient.temperature_c,
            "oxygen_saturation": patient.oxygen_saturation,
        }}

        await AuditLogger.log_update(
            resource=AuditResource.PATIENT,
            resource_id=patient.id,
            resource_identifier=patient.mrn,
            user_id=updated_by.id,
            user_role=updated_by.role.value,
            user_email=updated_by.email,
            description=f"Patient vitals updated: {patient.mrn}",
            old_values=old_values,
            new_values=new_values,
        )

        return patient

    async def delete_patient(self, patient_id: UUID, deleted_by: User) -> bool:
        """Soft delete patient."""
        patient = await self.get_patient(patient_id)
        await patient.soft_delete(deleted_by.id)

        await AuditLogger.log_delete(
            resource=AuditResource.PATIENT,
            resource_id=patient.id,
            resource_identifier=patient.mrn,
            user_id=deleted_by.id,
            user_role=deleted_by.role.value,
            user_email=deleted_by.email,
            description=f"Patient deleted: {patient.mrn}",
            old_values={"mrn": patient.mrn},
        )

        return True

    async def list_patients(self, params) -> List[Patient]:
        """List patients with pagination."""
        return await self.repo.list(params)

    async def search_patients(self, query: str, params) -> List[Patient]:
        """Search patients."""
        return await self.repo.search(query, params)

    async def get_patients_for_doctor(self, doctor_id: UUID, params) -> List[Patient]:
        """Get patients assigned to a doctor."""
        return await self.repo.get_by_doctor(doctor_id, params)

    async def get_dashboard_data(self, patient_id: UUID) -> dict:
        """Get patient dashboard data."""
        patient = await self.get_patient(patient_id)

        # Get upcoming appointments
        from app.repositories.encounter import encounter_repository
        upcoming = await encounter_repository.get_upcoming_for_patient(patient_id, limit=5)

        # Get recent documents
        from app.repositories.document import document_repository
        recent_docs = await document_repository.get_recent_for_patient(patient_id, limit=5)

        return {
            "patient": patient,
            "upcoming_appointments": upcoming,
            "recent_documents": recent_docs,
            "current_medications": patient.current_medications,
            "allergies": patient.allergies,
            "chronic_conditions": patient.chronic_conditions,
        }


patient_service = PatientService()