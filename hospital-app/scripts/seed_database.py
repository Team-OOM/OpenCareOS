"""
OpenCareOS - Database Seeding Script
Apache License 2.0
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from app.core.config.settings import get_settings
from app.core.database import init_database, get_database
from app.models.user import User, UserRole, UserStatus
from app.models.patient import Patient, Gender, BloodType, MaritalStatus
from app.models.encounter import Encounter, EncounterType, EncounterStatus, Priority
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.audit import AuditLog, AuditAction, AuditResource
from app.utils.helpers import generate_mrn, generate_confirmation_code


async def seed_database():
    """Seed database with dummy data."""
    print("Initializing database...")
    await init_database()

    print("Seeding users...")
    await seed_users()

    print("Seeding patients...")
    await seed_patients()

    print("Seeding encounters...")
    await seed_encounters()

    print("Seeding documents...")
    await seed_documents()

    print("Seeding audit logs...")
    await seed_audit_logs()

    print("Database seeding completed!")


async def seed_users():
    """Seed users."""
    # Admin user
    admin = User(
        id=uuid4(),
        email="admin@demo.com",
        username="admin",
        full_name="System Administrator",
        phone="+15551234567",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
        email_verified_at=datetime.utcnow(),
        hashed_password=User.hash_password("demo123"),
    )
    await admin.insert()

    # Doctor users
    doctors = [
        {
            "id": uuid4(),
            "email": "doctor@demo.com",
            "username": "drsarah",
            "full_name": "Dr. Sarah Johnson",
            "phone": "+15551234568",
            "role": UserRole.DOCTOR,
            "status": UserStatus.ACTIVE,
            "license_number": "MD123456",
            "specialization": "Cardiology",
            "department": "Cardiology",
            "qualifications": ["MD", "FACC"],
        },
        {
            "id": uuid4(),
            "email": "drmichael@demo.com",
            "username": "drmichael",
            "full_name": "Dr. Michael Chen",
            "phone": "+15551234569",
            "role": UserRole.DOCTOR,
            "status": UserStatus.ACTIVE,
            "license_number": "MD234567",
            "specialization": "Endocrinology",
            "department": "Endocrinology",
            "qualifications": ["MD", "FACE"],
        },
        {
            "id": uuid4(),
            "email": "drema@demo.com",
            "username": "drema",
            "full_name": "Dr. Emily Rodriguez",
            "phone": "+15551234570",
            "role": UserRole.DOCTOR,
            "status": UserStatus.ACTIVE,
            "license_number": "MD345678",
            "specialization": "Internal Medicine",
            "department": "Internal Medicine",
            "qualifications": ["MD", "FACP"],
        },
        {
            "id": uuid4(),
            "email": "drjames@demo.com",
            "username": "drjames",
            "full_name": "Dr. James Wilson",
            "phone": "+15551234571",
            "role": UserRole.DOCTOR,
            "status": UserStatus.ACTIVE,
            "license_number": "MD456789",
            "specialization": "Pulmonology",
            "department": "Pulmonology",
            "qualifications": ["MD", "FCCP"],
        },
        {
            "id": uuid4(),
            "email": "drlisa@demo.com",
            "username": "drlisa",
            "full_name": "Dr. Lisa Thompson",
            "phone": "+15551234572",
            "role": UserRole.DOCTOR,
            "status": UserStatus.ACTIVE,
            "license_number": "MD567890",
            "specialization": "Neurology",
            "department": "Neurology",
            "qualifications": ["MD", "FAAN"],
        },
    ]

    for doc_data in doctors:
        doctor = User(**doc_data)
        doctor.set_password("demo123")
        doctor.email_verified = True
        doctor.email_verified_at = datetime.utcnow()
        await doctor.save()

    # Patient users
    patients = [
        {
            "id": uuid4(),
            "email": "patient@demo.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "phone": "+15552234567",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "janesmith@demo.com",
            "username": "janesmith",
            "full_name": "Jane Smith",
            "phone": "+15552234568",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "robertbrown@demo.com",
            "username": "robertbrown",
            "full_name": "Robert Brown",
            "phone": "+15552234569",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "mariagarcia@demo.com",
            "username": "mariagarcia",
            "full_name": "Maria Garcia",
            "phone": "+15552234570",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "jameswilson@demo.com",
            "username": "jameswilson",
            "full_name": "James Wilson",
            "phone": "+15552234571",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "patricianderson@demo.com",
            "username": "patricianderson",
            "full_name": "Patricia Anderson",
            "phone": "+15552234572",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "michaeltaylor@demo.com",
            "username": "michaeltaylor",
            "full_name": "Michael Taylor",
            "phone": "+15552234573",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "lisamartinez@demo.com",
            "username": "lisamartinez",
            "full_name": "Lisa Martinez",
            "phone": "+15552234574",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "davidthompson@demo.com",
            "username": "davidthompson",
            "full_name": "David Thompson",
            "phone": "+15552234575",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
        {
            "id": uuid4(),
            "email": "sarahwhite@demo.com",
            "username": "sarahwhite",
            "full_name": "Sarah White",
            "phone": "+15552234576",
            "role": UserRole.PATIENT,
            "status": UserStatus.ACTIVE,
        },
    ]

    for pat_data in patients:
        patient = User(**pat_data)
        patient.set_password("demo123")
        patient.email_verified = True
        patient.email_verified_at = datetime.utcnow()
        await patient.save()

    print(f"Created {1 + len(doctors) + len(patients)} users")


async def seed_patients():
    """Seed patient records."""
    # Get patient users
    patient_users = await User.find({"role": UserRole.PATIENT, "is_deleted": {"$ne": True}}).to_list()

    # Get doctor users for primary_doctor_id
    doctor_users = await User.find({"role": UserRole.DOCTOR, "is_deleted": {"$ne": True}}).to_list()

    patient_data = [
        {
            "user_id": patient_users[0].id,
            "mrn": generate_mrn(),
            "date_of_birth": datetime(1972, 3, 15),
            "gender": Gender.MALE,
            "blood_type": BloodType.A_POS,
            "marital_status": MaritalStatus.MARRIED,
            "phone": "+15552234567",
            "email": "patient@demo.com",
            "address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_phone": "+15552234568",
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_policy_number": "BCBS123456789",
            "allergies": ["Penicillin", "Latex"],
            "chronic_conditions": ["Hypertension", "Type 2 Diabetes"],
            "current_medications": ["Atorvastatin 20mg", "Metoprolol 50mg", "Lisinopril 10mg"],
            "past_surgeries": ["Appendectomy (2005)"],
            "family_history": ["Father: Heart disease", "Mother: Diabetes"],
            "smoking_status": "former",
            "alcohol_consumption": "occasional",
            "exercise_frequency": "3 times/week",
            "height_cm": 175.0,
            "weight_kg": 82.0,
            "blood_pressure": "135/85",
            "heart_rate": 72,
            "temperature_c": 36.8,
            "oxygen_saturation": 98,
            "consent_given": True,
            "consent_date": datetime.utcnow() - timedelta(days=30),
            "primary_doctor_id": doctor_users[0].id,
            "preferred_language": "en",
            "preferred_contact_method": "phone",
        },
        {
            "user_id": patient_users[1].id,
            "mrn": generate_mrn(),
            "date_of_birth": datetime(1979, 7, 22),
            "gender": Gender.FEMALE,
            "blood_type": BloodType.O_POS,
            "marital_status": MaritalStatus.SINGLE,
            "phone": "+15552234568",
            "email": "janesmith@demo.com",
            "address": "456 Oak Ave",
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90001",
            "emergency_contact_name": "Mary Smith",
            "emergency_contact_relationship": "Mother",
            "emergency_contact_phone": "+15552234579",
            "insurance_provider": "Aetna",
            "insurance_policy_number": "AET987654321",
            "allergies": ["Sulfa drugs"],
            "chronic_conditions": ["Type 1 Diabetes", "Hypothyroidism"],
            "current_medications": ["Insulin Glargine", "Levothyroxine 75mcg", "Metformin 1000mg"],
            "past_surgeries": [],
            "family_history": ["Mother: Thyroid disease", "Sister: Type 1 Diabetes"],
            "smoking_status": "never",
            "alcohol_consumption": "none",
            "exercise_frequency": "daily",
            "height_cm": 165.0,
            "weight_kg": 60.0,
            "blood_pressure": "118/76",
            "heart_rate": 68,
            "temperature_c": 36.7,
            "oxygen_saturation": 99,
            "consent_given": True,
            "consent_date": datetime.utcnow() - timedelta(days=15),
            "primary_doctor_id": doctor_users[1].id,
            "preferred_language": "en",
            "preferred_contact_method": "email",
        },
        {
            "user_id": patient_users[2].id,
            "mrn": generate_mrn(),
            "date_of_birth": datetime(1957, 11, 8),
            "gender": Gender.MALE,
            "blood_type": BloodType.B_POS,
            "marital_status": MaritalStatus.MARRIED,
            "phone": "+15552234569",
            "email": "robertbrown@demo.com",
            "address": "789 Pine Rd",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60601",
            "emergency_contact_name": "Susan Brown",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_phone": "+15552234580",
            "insurance_provider": "Medicare",
            "insurance_policy_number": "MED123456789",
            "allergies": ["NKDA"],
            "chronic_conditions": ["COPD", "Hypertension", "Atrial Fibrillation"],
            "current_medications": ["Tiotropium 18mcg", "Metoprolol 100mg", "Apixaban 5mg", "Furosemide 20mg"],
            "past_surgeries": ["CABG (2018)", "Cataract surgery (2020)"],
            "family_history": ["Father: COPD", "Brother: Heart disease"],
            "smoking_status": "former",
            "alcohol_consumption": "none",
            "exercise_frequency": "limited",
            "height_cm": 170.0,
            "weight_kg": 78.0,
            "blood_pressure": "142/88",
            "heart_rate": 88,
            "temperature_c": 36.9,
            "oxygen_saturation": 94,
            "consent_given": True,
            "consent_date": datetime.utcnow() - timedelta(days=45),
            "primary_doctor_id": doctor_users[3].id,
            "preferred_language": "en",
            "preferred_contact_method": "phone",
        },
        {
            "user_id": patient_users[3].id,
            "mrn": generate_mrn(),
            "date_of_birth": datetime(1986, 5, 30),
            "gender": Gender.FEMALE,
            "blood_type": BloodType.AB_POS,
            "marital_status": MaritalStatus.MARRIED,
            "phone": "+15552234570",
            "email": "mariagarcia@demo.com",
            "address": "321 Elm St",
            "city": "Houston",
            "state": "TX",
            "postal_code": "77001",
            "emergency_contact_name": "Carlos Garcia",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_phone": "+15552234581",
            "insurance_provider": "Cigna",
            "insurance_policy_number": "CIG567890123",
            "allergies": ["Iodine", "Shellfish"],
            "chronic_conditions": ["Asthma", "Allergic Rhinitis"],
            "current_medications": ["Fluticasone nasal spray", "Albuterol inhaler PRN", "Cetirizine 10mg"],
            "past_surgeries": ["Tonsillectomy (2000)"],
            "family_history": ["Mother: Asthma", "Father: Allergies"],
            "smoking_status": "never",
            "alcohol_consumption": "social",
            "exercise_frequency": "4 times/week",
            "height_cm": 162.0,
            "weight_kg": 58.0,
            "blood_pressure": "110/70",
            "heart_rate": 65,
            "temperature_c": 36.6,
            "oxygen_saturation": 99,
            "consent_given": True,
            "consent_date": datetime.utcnow() - timedelta(days=60),
            "primary_doctor_id": doctor_users[2].id,
            "preferred_language": "es",
            "preferred_contact_method": "phone",
        },
        {
            "user_id": patient_users[4].id,
            "mrn": generate_mrn(),
            "date_of_birth": datetime(1969, 9, 12),
            "gender": Gender.MALE,
            "blood_type": BloodType.O_NEG,
            "marital_status": MaritalStatus.DIVORCED,
            "phone": "+15552234571",
            "email": "jameswilson@demo.com",
            "address": "555 Cedar Ln",
            "city": "Phoenix",
            "state": "AZ",
            "postal_code": "85001",
            "emergency_contact_name": "Jennifer Wilson",
            "emergency_contact_relationship": "Daughter",
            "emergency_contact_phone": "+15552234582",
            "insurance_provider": "UnitedHealthcare",
            "insurance_policy_number": "UHC345678901",
            "allergies": ["Aspirin"],
            "chronic_conditions": ["Chronic Kidney Disease Stage 3", "Hypertension"],
            "current_medications": ["Losartan 50mg", "Calcium carbonate", "Erythropoietin"],
            "past_surgeries": ["AV fistula creation (2022)"],
            "family_history": ["Mother: Kidney disease"],
            "smoking_status": "never",
            "alcohol_consumption": "none",
            "exercise_frequency": "2 times/week",
            "height_cm": 178.0,
            "weight_kg": 85.0,
            "blood_pressure": "138/82",
            "heart_rate": 70,
            "temperature_c": 36.8,
            "oxygen_saturation": 97,
            "consent_given": True,
            "consent_date": datetime.utcnow() - timedelta(days=20),
            "primary_doctor_id": doctor_users[1].id,
            "preferred_language": "en",
            "preferred_contact_method": "email",
        },
    ]

    for i, data in enumerate(patient_data):
        if i < len(patient_users):
            patient = Patient(**data)
            patient.update_bmi()
            await patient.insert()

    # Create remaining patients with minimal data
    for i in range(5, min(len(patient_users), 10)):
        patient = Patient(
            user_id=patient_users[i].id,
            mrn=generate_mrn(),
            date_of_birth=datetime(1980 + (i * 3) % 40, (i % 12) + 1, (i % 28) + 1),
            gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
            blood_type=list(BloodType)[i % len(BloodType)],
            phone=patient_users[i].phone,
            email=patient_users[i].email,
            primary_doctor_id=doctor_users[i % len(doctor_users)].id,
            consent_given=True,
            consent_date=datetime.utcnow() - timedelta(days=30),
        )
        await patient.insert()

    print(f"Created {min(len(patient_users), 10)} patient records")


async def seed_encounters():
    """Seed encounters/appointments."""
    patients = await Patient.find({"is_deleted": {"$ne": True}}).to_list()
    doctors = await User.find({"role": UserRole.DOCTOR, "is_deleted": {"$ne": True}}).to_list()

    encounter_types = list(EncounterType)
    statuses = list(EncounterStatus)
    priorities = list(Priority)

    base_date = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        patient = patients[i % len(patients)]
        doctor = doctors[i % len(doctors)]

        scheduled_at = base_date + timedelta(days=i, hours=(i % 8) + 9, minutes=(i % 4) * 15)

        encounter = Encounter(
            patient_id=patient.id,
            doctor_id=doctor.id,
            encounter_type=encounter_types[i % len(encounter_types)],
            status=statuses[i % len(statuses)] if i < 25 else EncounterStatus.SCHEDULED,
            priority=priorities[i % len(priorities)],
            scheduled_at=scheduled_at,
            duration_minutes=30 if i % 3 != 0 else 45,
            chief_complaint=[
                "Chest pain follow-up",
                "Diabetes management",
                "Hypertension review",
                "Annual checkup",
                "Medication refill",
                "Shortness of breath",
                "Headache evaluation",
                "Joint pain",
                "Skin rash",
                "Fatigue",
            ][i % 10],
            location=f"{doctor.specialization} Clinic, Room {(i % 10) + 100}",
            is_virtual=(i % 5 == 0),
            virtual_meeting_url=f"https://meet.opencareos.org/{generate_confirmation_code('VC')}" if i % 5 == 0 else None,
            notes=f"Routine follow-up visit. Patient reports feeling well. No new symptoms." if i % 2 == 0 else None,
        )

        # Set timestamps based on status
        if encounter.status in [EncounterStatus.COMPLETED, EncounterStatus.CHECKED_IN, EncounterStatus.IN_PROGRESS]:
            encounter.checked_in_at = scheduled_at - timedelta(minutes=15)
        if encounter.status in [EncounterStatus.IN_PROGRESS, EncounterStatus.COMPLETED]:
            encounter.started_at = scheduled_at
        if encounter.status == EncounterStatus.COMPLETED:
            encounter.completed_at = scheduled_at + timedelta(minutes=encounter.duration_minutes)
        if encounter.status == EncounterStatus.CANCELLED:
            encounter.cancelled_at = scheduled_at - timedelta(hours=2)
            encounter.cancellation_reason = "Patient requested rescheduling"

        await encounter.insert()

    print("Created 30 encounters")


async def seed_documents():
    """Seed documents."""
    patients = await Patient.find({"is_deleted": {"$ne": True}}).to_list()
    doctors = await User.find({"role": UserRole.DOCTOR, "is_deleted": {"$ne": True}}).to_list()

    doc_types = list(DocumentType)
    statuses = list(DocumentStatus)

    for i in range(20):
        patient = patients[i % len(patients)]
        doctor = doctors[i % len(doctors)]

        document = Document(
            patient_id=patient.id,
            uploaded_by_id=doctor.id,
            document_type=doc_types[i % len(doc_types)],
            status=DocumentStatus.FINAL,
            title=[
                "Lipid Panel Results",
                "HbA1c Report",
                "Basic Metabolic Panel",
                "Chest X-Ray Report",
                "ECG Results",
                "Thyroid Function Tests",
                "CBC with Differential",
                "Liver Function Tests",
                "Renal Function Panel",
                "Urinalysis Results",
                "Echocardiogram Report",
                "Pulmonary Function Test",
                "MRI Brain Report",
                "CT Abdomen Report",
                "Doppler Ultrasound",
                "Pathology Report",
                "Prescription Record",
                "Discharge Summary",
                "Referral Letter",
                "Vaccination Record",
            ][i],
            description=f"Routine {doc_types[i % len(doc_types)].value.replace('_', ' ')} for patient follow-up",
            file_name=f"{doc_types[i % len(doc_types)].value}_{i+1}.pdf",
            file_path=f"/app/uploads/{doc_types[i % len(doc_types)].value}_{i+1}.pdf",
            file_size=1024 * (500 + i * 100),
            mime_type="application/pdf",
            file_hash=f"sha256_{'a' * 64}",
            tags=["routine", "follow-up"],
            category="laboratory" if "lab" in doc_types[i % len(doc_types)].value else "imaging",
            version=1,
        )
        await document.insert()

    print("Created 20 documents")


async def seed_audit_logs():
    """Seed audit logs."""
    admin = await User.find_one({"email": "admin@demo.com"})
    patients = await Patient.find({"is_deleted": {"$ne": True}}).limit(3).to_list()
    doctors = await User.find({"role": UserRole.DOCTOR, "is_deleted": {"$ne": True}}).limit(2).to_list()

    logs = [
        {
            "action": AuditAction.CREATE,
            "resource": AuditResource.USER,
            "description": "Admin user created",
            "user_id": admin.id,
            "user_role": "admin",
            "user_email": admin.email,
            "success": True,
        },
        {
            "action": AuditAction.LOGIN,
            "resource": AuditResource.USER,
            "description": "User logged in",
            "user_id": doctors[0].id,
            "user_role": "doctor",
            "user_email": doctors[0].email,
            "success": True,
            "ip_address": "192.168.1.100",
        },
        {
            "action": AuditAction.CREATE,
            "resource": AuditResource.PATIENT,
            "description": "Patient record created",
            "user_id": doctors[0].id,
            "user_role": "doctor",
            "user_email": doctors[0].email,
            "success": True,
            "is_phi_access": True,
        },
        {
            "action": AuditAction.READ,
            "resource": AuditResource.PATIENT,
            "description": "Patient chart accessed",
            "user_id": doctors[0].id,
            "user_role": "doctor",
            "user_email": doctors[0].email,
            "resource_id": patients[0].id,
            "success": True,
            "is_phi_access": True,
        },
        {
            "action": AuditAction.CREATE,
            "resource": AuditResource.APPOINTMENT,
            "description": "Appointment booked",
            "user_id": patients[0].user_id,
            "user_role": "patient",
            "user_email": patients[0].email,
            "success": True,
        },
        {
            "action": AuditAction.AI_INTERACTION,
            "resource": AuditResource.SYSTEM,
            "description": "AI chat interaction",
            "user_id": patients[0].user_id,
            "user_role": "patient",
            "user_email": patients[0].email,
            "success": True,
            "is_phi_access": True,
            "details": {"conversation_id": "conv-123", "tools_used": ["check_availability"]},
        },
    ]

    for log_data in logs:
        log = AuditLog(**log_data)
        await log.insert()

    print(f"Created {len(logs)} audit logs")


if __name__ == "__main__":
    asyncio.run(seed_database())