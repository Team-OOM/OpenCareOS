"""
OpenCareOS - AI Services (Placeholder Interfaces)
Apache License 2.0
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from dataclasses import dataclass
from abc import ABC, abstractmethod
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.document import Document
from app.models.user import User


@dataclass
class DrugInteractionResult:
    """Result of drug interaction check."""
    drug_a: str
    drug_b: str
    severity: str  # "mild", "moderate", "severe", "contraindicated"
    description: str
    recommendation: str
    evidence_level: str = "C"  # A, B, C, D
    mechanism: Optional[str] = None


@dataclass
class PatientSummaryResult:
    """Result of patient history summarization."""
    patient_id: UUID
    summary: str
    key_conditions: List[str]
    current_medications: List[str]
    allergies: List[str]
    recent_encounters: List[Dict[str, Any]]
    risk_factors: List[str]
    care_gaps: List[str]


@dataclass
class MedicalRecommendationResult:
    """Result of medical recommendation."""
    recommendation_type: str  # "diagnosis", "treatment", "follow_up", "referral", "test"
    title: str
    description: str
    confidence: float  # 0.0 - 1.0
    urgency: str  # "routine", "urgent", "emergency"
    supporting_evidence: List[str]
    suggested_actions: List[str]


@dataclass
class ChatResponse:
    """AI chat response."""
    message: str
    tool_calls: List[Dict[str, Any]] = None
    thinking: Optional[str] = None
    citations: List[Dict[str, Any]] = None


class DrugInteractionService(ABC):
    """Service for checking drug interactions."""

    @abstractmethod
    async def check_interaction(
        self,
        drug_a: str,
        drug_b: str,
        patient: Optional[Patient] = None,
    ) -> DrugInteractionResult:
        """Check interaction between two drugs."""
        pass

    @abstractmethod
    async def check_multiple_interactions(
        self,
        medications: List[str],
        patient: Optional[Patient] = None,
    ) -> List[DrugInteractionResult]:
        """Check interactions among multiple medications."""
        pass

    @abstractmethod
    async def get_drug_info(self, drug_name: str) -> Dict[str, Any]:
        """Get drug information."""
        pass


class MockDrugInteractionService(DrugInteractionService):
    """Mock implementation for development."""

    # Known interactions for demo
    INTERACTIONS = {
        ("warfarin", "aspirin"): DrugInteractionResult(
            drug_a="Warfarin",
            drug_b="Aspirin",
            severity="severe",
            description="Increased risk of bleeding due to combined anticoagulant and antiplatelet effects",
            recommendation="Avoid combination. If necessary, monitor INR closely and consider alternative analgesic.",
            evidence_level="A",
            mechanism="Both drugs inhibit platelet aggregation and affect coagulation cascade",
        ),
        ("metformin", "contrast"): DrugInteractionResult(
            drug_a="Metformin",
            drug_b="Iodinated Contrast",
            severity="moderate",
            description="Risk of lactic acidosis due to contrast-induced nephropathy reducing metformin clearance",
            recommendation="Hold metformin 48 hours before and after contrast administration. Check renal function before restarting.",
            evidence_level="B",
            mechanism="Contrast media can cause acute kidney injury, reducing metformin elimination",
        ),
        ("lisinopril", "potassium"): DrugInteractionResult(
            drug_a="Lisinopril",
            drug_b="Potassium Supplements",
            severity="moderate",
            description="ACE inhibitors can increase serum potassium; risk of hyperkalemia with potassium supplements",
            recommendation="Monitor serum potassium regularly. Consider reducing or discontinuing potassium supplements.",
            evidence_level="B",
            mechanism="ACE inhibitors reduce aldosterone, decreasing potassium excretion",
        ),
        ("simvastatin", "clarithromycin"): DrugInteractionResult(
            drug_a="Simvastatin",
            drug_b="Clarithromycin",
            severity="severe",
            description="Clarithromycin strongly inhibits CYP3A4, increasing simvastatin levels and risk of rhabdomyolysis",
            recommendation="Contraindicated. Use alternative antibiotic or switch to non-CYP3A4 metabolized statin.",
            evidence_level="A",
            mechanism="CYP3A4 inhibition by clarithromycin reduces simvastatin metabolism",
        ),
    }

    async def check_interaction(
        self,
        drug_a: str,
        drug_b: str,
        patient: Optional[Patient] = None,
    ) -> DrugInteractionResult:
        """Check interaction between two drugs."""
        key = tuple(sorted([drug_a.lower(), drug_b.lower()]))
        return self.INTERACTIONS.get(key, DrugInteractionResult(
            drug_a=drug_a,
            drug_b=drug_b,
            severity="none",
            description="No significant interaction known",
            recommendation="No specific monitoring required",
            evidence_level="C",
        ))

    async def check_multiple_interactions(
        self,
        medications: List[str],
        patient: Optional[Patient] = None,
    ) -> List[DrugInteractionResult]:
        """Check interactions among multiple medications."""
        results = []
        for i, drug_a in enumerate(medications):
            for drug_b in medications[i+1:]:
                result = await self.check_interaction(drug_a, drug_b, patient)
                if result.severity != "none":
                    results.append(result)
        return results

    async def get_drug_info(self, drug_name: str) -> Dict[str, Any]:
        """Get drug information."""
        # Mock data
        return {
            "name": drug_name,
            "generic_name": drug_name.lower(),
            "class": "Unknown",
            "indications": [],
            "contraindications": [],
            "side_effects": [],
            "dosage": "Consult prescribing information",
        }


class PatientSummaryService(ABC):
    """Service for generating patient history summaries."""

    @abstractmethod
    async def generate_summary(
        self,
        patient: Patient,
        encounters: List[Encounter],
        documents: List[Document],
    ) -> PatientSummaryResult:
        """Generate patient history summary."""
        pass


class MockPatientSummaryService(PatientSummaryService):
    """Mock implementation for development."""

    async def generate_summary(
        self,
        patient: Patient,
        encounters: List[Encounter],
        documents: List[Document],
    ) -> PatientSummaryResult:
        """Generate patient history summary."""
        # Extract key info
        conditions = patient.chronic_conditions
        medications = patient.current_medications
        allergies = patient.allergies

        recent_encounters = []
        for enc in encounters[:5]:
            recent_encounters.append({
                "date": enc.scheduled_at.isoformat() if enc.scheduled_at else None,
                "type": enc.encounter_type.value,
                "chief_complaint": enc.chief_complaint,
                "diagnosis": enc.diagnosis,
                "doctor": str(enc.doctor_id),
            })

        return PatientSummaryResult(
            patient_id=patient.id,
            summary=f"{patient.mrn} is a {patient.age}-year-old {patient.gender.value} with "
                    f"{', '.join(conditions) if conditions else 'no known chronic conditions'}. "
                    f"Currently on {', '.join(medications) if medications else 'no medications'}. "
                    f"Allergies: {', '.join(allergies) if allergies else 'NKDA'}.",
            key_conditions=conditions,
            current_medications=medications,
            allergies=allergies,
            recent_encounters=recent_encounters,
            risk_factors=self._identify_risk_factors(patient),
            care_gaps=self._identify_care_gaps(patient, encounters),
        )

    def _identify_risk_factors(self, patient: Patient) -> List[str]:
        """Identify risk factors."""
        factors = []
        if patient.age > 65:
            factors.append("Advanced age")
        if patient.bmi and patient.bmi > 30:
            factors.append("Obesity")
        if patient.smoking_status == "current":
            factors.append("Current smoker")
        if "diabetes" in [c.lower() for c in patient.chronic_conditions]:
            factors.append("Diabetes mellitus")
        if "hypertension" in [c.lower() for c in patient.chronic_conditions]:
            factors.append("Hypertension")
        return factors

    def _identify_care_gaps(
        self,
        patient: Patient,
        encounters: List[Encounter],
    ) -> List[str]:
        """Identify care gaps."""
        gaps = []
        # Check for recent visits
        recent = [e for e in encounters if e.status == "completed"]
        if not recent:
            gaps.append("No recent follow-up visits")
        # Check for age-appropriate screening
        if patient.age > 50 and patient.gender.value == "female":
            gaps.append("Consider mammography screening")
        if patient.age > 45:
            gaps.append("Consider colorectal cancer screening")
        return gaps


class MedicalRecommendationService(ABC):
    """Service for generating medical recommendations."""

    @abstractmethod
    async def get_recommendations(
        self,
        patient: Patient,
        encounter: Encounter,
        context: Dict[str, Any],
    ) -> List[MedicalRecommendationResult]:
        """Get medical recommendations for an encounter."""
        pass


class MockMedicalRecommendationService(MedicalRecommendationService):
    """Mock implementation for development."""

    async def get_recommendations(
        self,
        patient: Patient,
        encounter: Encounter,
        context: Dict[str, Any],
    ) -> List[MedicalRecommendationResult]:
        """Get medical recommendations."""
        recommendations = []

        # Based on chief complaint
        if encounter.chief_complaint:
            complaint = encounter.chief_complaint.lower()
            if "chest pain" in complaint:
                recommendations.append(MedicalRecommendationResult(
                    recommendation_type="test",
                    title="ECG and Troponin",
                    description="Rule out acute coronary syndrome",
                    confidence=0.9,
                    urgency="emergency",
                    supporting_evidence=["Chest pain protocol", "ACC/AHA guidelines"],
                    suggested_actions=["Order STAT ECG", "Serial troponins", "Cardiology consult if positive"],
                ))
            elif "shortness of breath" in complaint:
                recommendations.append(MedicalRecommendationResult(
                    recommendation_type="test",
                    title="Chest X-ray and BNP",
                    description="Evaluate for heart failure or pneumonia",
                    confidence=0.8,
                    urgency="urgent",
                    supporting_evidence=["Heart failure guidelines", "Pneumonia workup"],
                    suggested_actions=["Order CXR", "Check BNP", "Consider echocardiogram"],
                ))

        # Based on chronic conditions
        if "diabetes" in [c.lower() for c in patient.chronic_conditions]:
            recommendations.append(MedicalRecommendationResult(
                recommendation_type="follow_up",
                title="Diabetes Management",
                description="Optimize glycemic control",
                confidence=0.9,
                urgency="routine",
                supporting_evidence=["ADA Standards of Care"],
                suggested_actions=["Check HbA1c", "Review medications", "Foot exam", "Eye exam referral"],
            ))

        if "hypertension" in [c.lower() for c in patient.chronic_conditions]:
            recommendations.append(MedicalRecommendationResult(
                recommendation_type="follow_up",
                title="Hypertension Management",
                description="Blood pressure control",
                confidence=0.9,
                urgency="routine",
                supporting_evidence=["ACC/AHA Hypertension Guidelines"],
                suggested_actions=["Check BP", "Review medications", "Lifestyle counseling", "Home BP monitoring"],
            ))

        return recommendations


class AIChatService(ABC):
    """Service for AI chat interactions."""

    @abstractmethod
    async def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        patient: Optional[Patient] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Process chat message and return response."""
        pass


class MockAIChatService(AIChatService):
    """Mock implementation for development."""

    async def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        patient: Optional[Patient] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """Process chat message."""
        # Simple mock responses based on keywords
        message_lower = message.lower()

        if "appointment" in message_lower or "book" in message_lower:
            return ChatResponse(
                message="I can help you book an appointment. Would you like me to check available slots with your doctor?",
                tool_calls=[{
                    "name": "check_doctor_availability",
                    "arguments": {"doctor_id": "current_doctor", "date": "next_week"},
                }],
            )
        elif "medication" in message_lower or "prescription" in message_lower:
            return ChatResponse(
                message="I can check your current medications and any potential interactions. Let me look that up for you.",
                tool_calls=[{
                    "name": "get_patient_medications",
                    "arguments": {"patient_id": str(patient.id) if patient else "current"},
                }],
            )
        elif "report" in message_lower or "result" in message_lower:
            return ChatResponse(
                message="I can help you access your recent lab reports and imaging results. Which type of report are you looking for?",
            )
        else:
            return ChatResponse(
                message="I'm here to help with your healthcare needs. You can ask me about appointments, medications, test results, or general health questions.",
            )


# Service instances
drug_interaction_service: DrugInteractionService = MockDrugInteractionService()
patient_summary_service: PatientSummaryService = MockPatientSummaryService()
medical_recommendation_service: MedicalRecommendationService = MockMedicalRecommendationService()
ai_chat_service: AIChatService = MockAIChatService()