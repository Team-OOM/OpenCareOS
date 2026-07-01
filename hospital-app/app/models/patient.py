"""
OpenCareOS - Patient Model
Apache License 2.0
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import Field, EmailStr, ConfigDict
from beanie import Document, Indexed, PydanticObjectId, Link
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from app.models.base import BaseDocument
from app.models.user import User


class Gender(str, Enum):
    """Patient gender."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class BloodType(str, Enum):
    """Blood types."""

    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"
    UNKNOWN = "unknown"


class MaritalStatus(str, Enum):
    """Marital status."""

    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"


class Patient(BaseDocument):
    """Patient model with medical information."""

    # Link to user account
    user_id: Indexed(Link[User], unique=True)

    # Medical identifiers
    mrn: Indexed(str, unique=True)  # Medical Record Number
    external_id: Optional[str] = None  # External system ID

    # Demographics
    date_of_birth: datetime
    gender: Gender
    blood_type: BloodType = BloodType.UNKNOWN
    marital_status: MaritalStatus = MaritalStatus.SINGLE

    # Contact
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "India"

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

    # Vitals (latest)
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    oxygen_saturation: Optional[int] = None

    # Consent
    consent_given: bool = False
    consent_date: Optional[datetime] = None
    consent_version: str = "1.0"

    # Care team
    primary_doctor_id: Optional[Link[User]] = None
    assigned_nurse_id: Optional[Link[User]] = None

    # Preferences
    preferred_language: str = "en"
    preferred_contact_method: str = "phone"
    notification_preferences: dict = {}

    class Settings:
        name = "patients"
        indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True),
            IndexModel([("mrn", ASCENDING)], unique=True),
            IndexModel([("external_id", ASCENDING)]),
            IndexModel([("date_of_birth", ASCENDING)]),
            IndexModel([("gender", ASCENDING)]),
            IndexModel([("blood_type", ASCENDING)]),
            IndexModel([("primary_doctor_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("full_name", TEXT), ("mrn", TEXT), ("email", TEXT), ("phone", TEXT)]),
        ]
        use_state_management = True

    @property
    def age(self) -> int:
        """Calculate age from date of birth."""
        today = datetime.utcnow().date()
        dob = self.date_of_birth.date() if isinstance(self.date_of_birth, datetime) else self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def is_minor(self) -> bool:
        """Check if patient is a minor (< 18 years)."""
        return self.age < 18

    def update_bmi(self) -> None:
        """Calculate and update BMI."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m * height_m), 1)