"""
OpenCareOS - Patient Schemas
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from app.models.patient import Gender, BloodType, MaritalStatus
from app.schemas.base import BaseSchema, PaginationParams, PaginatedResponse


# --- Request Schemas ---

class PatientCreateRequest(BaseSchema):
    """Patient creation request."""

    user_id: UUID = Field(..., description="Linked user ID")
    mrn: str = Field(..., min_length=1, max_length=50, description="Medical Record Number")
    external_id: Optional[str] = Field(default=None, max_length=100)

    # Demographics
    date_of_birth: datetime = Field(..., description="Date of birth")
    gender: Gender
    blood_type: BloodType = BloodType.UNKNOWN
    marital_status: MaritalStatus = MaritalStatus.SINGLE

    # Contact
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")

    # Insurance
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    insurance_expiry: Optional[datetime] = None

    # Medical history
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    past_surgeries: List[str] = []
    family_history: List[str] = []

    # Lifestyle
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    exercise_frequency: Optional[str] = None

    # Vitals
    height_cm: Optional[float] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = Field(default=None, gt=0, le=300)
    temperature_c: Optional[float] = Field(default=None, ge=30, le=45)
    oxygen_saturation: Optional[int] = Field(default=None, ge=50, le=100)

    # Consent
    consent_given: bool = False
    consent_version: str = "1.0"

    # Care team
    primary_doctor_id: Optional[UUID] = None
    assigned_nurse_id: Optional[UUID] = None

    # Preferences
    preferred_language: str = "en"
    preferred_contact_method: str = "phone"
    notification_preferences: dict = {}


class PatientUpdateRequest(BaseSchema):
    """Patient update request."""

    mrn: Optional[str] = Field(default=None, min_length=1, max_length=50)
    external_id: Optional[str] = None

    # Demographics
    date_of_birth: Optional[datetime] = None
    gender: Optional[Gender] = None
    blood_type: Optional[BloodType] = None
    marital_status: Optional[MaritalStatus] = None

    # Contact
    phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")

    # Insurance
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    insurance_expiry: Optional[datetime] = None

    # Medical history
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    past_surgeries: Optional[List[str]] = None
    family_history: Optional[List[str]] = None

    # Lifestyle
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    exercise_frequency: Optional[str] = None

    # Vitals
    height_cm: Optional[float] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = Field(default=None, gt=0, le=300)
    temperature_c: Optional[float] = Field(default=None, ge=30, le=45)
    oxygen_saturation: Optional[int] = Field(default=None, ge=50, le=100)

    # Consent
    consent_given: Optional[bool] = None
    consent_version: Optional[str] = None

    # Care team
    primary_doctor_id: Optional[UUID] = None
    assigned_nurse_id: Optional[UUID] = None

    # Preferences
    preferred_language: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    notification_preferences: Optional[dict] = None


class VitalsUpdateRequest(BaseSchema):
    """Vitals update request."""

    height_cm: Optional[float] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = Field(default=None, gt=0, le=300)
    temperature_c: Optional[float] = Field(default=None, ge=30, le=45)
    oxygen_saturation: Optional[int] = Field(default=None, ge=50, le=100)


# --- Response Schemas ---

class PatientResponse(BaseSchema):
    """Patient response."""

    id: UUID
    user_id: UUID
    mrn: str
    external_id: Optional[str] = None

    # Demographics
    date_of_birth: datetime
    gender: Gender
    blood_type: BloodType
    marital_status: MaritalStatus

    # Contact
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str

    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    # Insurance
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    insurance_expiry: Optional[datetime] = None

    # Medical history
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    past_surgeries: List[str] = []
    family_history: List[str] = []

    # Lifestyle
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    exercise_frequency: Optional[str] = None

    # Vitals
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    oxygen_saturation: Optional[int] = None

    # Consent
    consent_given: bool
    consent_date: Optional[datetime] = None
    consent_version: str

    # Care team
    primary_doctor_id: Optional[UUID] = None
    assigned_nurse_id: Optional[UUID] = None

    # Preferences
    preferred_language: str
    preferred_contact_method: str
    notification_preferences: dict = {}

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Computed
    age: int
    is_minor: bool


class PatientSummaryResponse(BaseSchema):
    """Patient summary for lists and references."""

    id: UUID
    mrn: str
    full_name: str  # From user
    date_of_birth: datetime
    gender: Gender
    age: int
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    blood_type: BloodType
    primary_doctor_id: Optional[UUID] = None
    created_at: datetime


class PatientListResponse(BaseSchema):
    """Patient list response."""

    patients: List[PatientSummaryResponse]
    total: int
    page: int
    size: int
    pages: int


class PatientDashboardResponse(BaseSchema):
    """Patient dashboard response."""

    patient: PatientSummaryResponse
    upcoming_appointments: List["AppointmentSummaryResponse"] = []
    recent_reports: List["DocumentSummaryResponse"] = []
    current_medications: List["MedicationSummaryResponse"] = []
    health_metrics: dict = {}


# Forward references - will be defined in other schema files
class AppointmentSummaryResponse(BaseSchema):
    id: UUID
    scheduled_at: datetime
    status: str
    doctor_name: str
    department: Optional[str] = None
    encounter_type: str


class DocumentSummaryResponse(BaseSchema):
    id: UUID
    title: str
    document_type: str
    created_at: datetime


class MedicationSummaryResponse(BaseSchema):
    id: UUID
    name: str
    dosage: str
    frequency: str
    status: str


# Update forward references
PatientDashboardResponse.model_rebuild()