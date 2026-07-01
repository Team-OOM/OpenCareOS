"""
OpenCareOS - AI API Router
Apache License 2.0
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from pydantic import BaseModel, Field
from app.core.exceptions import NotFoundError, ValidationError, open_care_exception_to_http
from app.schemas.base import APIResponse
from app.services.ai import (
    drug_interaction_service,
    patient_summary_service,
    medical_recommendation_service,
    ai_chat_service,
    DrugInteractionResult,
    PatientSummaryResult,
    MedicalRecommendationResult,
    ChatResponse,
)
from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.document import Document
from app.api.routers.auth import get_current_active_user

router = APIRouter(prefix="/api/ai", tags=["AI Services"])


# --- Request/Response Models ---

class DrugInteractionRequest(BaseModel):
    drug_a: str = Field(..., min_length=1)
    drug_b: str = Field(..., min_length=1)
    patient_id: Optional[UUID] = None


class DrugInteractionResponse(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    description: str
    recommendation: str
    evidence_level: str
    mechanism: Optional[str] = None


class MultipleDrugInteractionRequest(BaseModel):
    medications: List[str] = Field(..., min_length=2)
    patient_id: Optional[UUID] = None


class PatientSummaryRequest(BaseModel):
    patient_id: UUID


class MedicalRecommendationRequest(BaseModel):
    encounter_id: UUID
    context: dict = Field(default_factory=dict)


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_history: List[dict] = Field(default_factory=list)
    patient_id: Optional[UUID] = None
    context: dict = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    message: str
    tool_calls: List[dict] = Field(default_factory=list)
    thinking: Optional[str] = None
    citations: List[dict] = Field(default_factory=list)


# --- Drug Interaction Endpoints ---

@router.post("/drug-interaction/check", response_model=APIResponse[DrugInteractionResponse])
async def check_drug_interaction(
    request: DrugInteractionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Check interaction between two drugs."""
    try:
        patient = None
        if request.patient_id:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient(request.patient_id)

        result = await drug_interaction_service.check_interaction(
            request.drug_a,
            request.drug_b,
            patient,
        )

        return APIResponse.success_response(
            data=DrugInteractionResponse(
                drug_a=result.drug_a,
                drug_b=result.drug_b,
                severity=result.severity,
                description=result.description,
                recommendation=result.recommendation,
                evidence_level=result.evidence_level,
                mechanism=result.mechanism,
            ),
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/drug-interaction/check-multiple", response_model=APIResponse[List[DrugInteractionResponse]])
async def check_multiple_drug_interactions(
    request: MultipleDrugInteractionRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Check interactions among multiple medications."""
    try:
        patient = None
        if request.patient_id:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient(request.patient_id)

        results = await drug_interaction_service.check_multiple_interactions(
            request.medications,
            patient,
        )

        return APIResponse.success_response(
            data=[
                DrugInteractionResponse(
                    drug_a=r.drug_a,
                    drug_b=r.drug_b,
                    severity=r.severity,
                    description=r.description,
                    recommendation=r.recommendation,
                    evidence_level=r.evidence_level,
                    mechanism=r.mechanism,
                )
                for r in results
            ],
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.get("/drug-info/{drug_name}", response_model=APIResponse[dict])
async def get_drug_info(
    drug_name: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get drug information."""
    try:
        info = await drug_interaction_service.get_drug_info(drug_name)
        return APIResponse.success_response(data=info)
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


# --- Patient Summary Endpoints ---

@router.post("/patient/summary", response_model=APIResponse[dict])
async def generate_patient_summary(
    request: PatientSummaryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Generate AI summary of patient history (doctors only)."""
    if not current_user.is_doctor and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only doctors can access patient summaries")

    try:
        from app.services.patient import patient_service
        from app.repositories.encounter import encounter_repository
        from app.repositories.document import document_repository

        patient = await patient_service.get_patient(request.patient_id)
        encounters = await encounter_repository.get_by_patient(request.patient_id, limit=20)
        documents = await document_repository.get_by_patient(request.patient_id, limit=20)

        result = await patient_summary_service.generate_summary(patient, encounters, documents)

        return APIResponse.success_response(
            data={
                "patient_id": str(result.patient_id),
                "summary": result.summary,
                "key_conditions": result.key_conditions,
                "current_medications": result.current_medications,
                "allergies": result.allergies,
                "recent_encounters": result.recent_encounters,
                "risk_factors": result.risk_factors,
                "care_gaps": result.care_gaps,
            },
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


# --- Medical Recommendations Endpoints ---

@router.post("/recommendations", response_model=APIResponse[List[dict]])
async def get_medical_recommendations(
    request: MedicalRecommendationRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Get AI medical recommendations for an encounter (doctors only)."""
    if not current_user.is_doctor and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only doctors can access recommendations")

    try:
        from app.repositories.encounter import encounter_repository
        from app.services.patient import patient_service

        encounter = await encounter_repository.get_by_id(request.encounter_id)
        if not encounter:
            raise NotFoundError("Encounter", str(request.encounter_id))

        if encounter.doctor_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized for this encounter")

        patient = await patient_service.get_patient(encounter.patient_id)
        results = await medical_recommendation_service.get_recommendations(
            patient,
            encounter,
            request.context,
        )

        return APIResponse.success_response(
            data=[
                {
                    "recommendation_type": r.recommendation_type,
                    "title": r.title,
                    "description": r.description,
                    "confidence": r.confidence,
                    "urgency": r.urgency,
                    "supporting_evidence": r.supporting_evidence,
                    "suggested_actions": r.suggested_actions,
                }
                for r in results
            ],
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


# --- Chat Endpoints ---

@router.post("/chat", response_model=APIResponse[ChatMessageResponse])
async def chat_with_ai(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Chat with AI assistant."""
    try:
        patient = None
        if request.patient_id:
            from app.services.patient import patient_service
            patient = await patient_service.get_patient(request.patient_id)

            # Check permissions
            if current_user.is_patient:
                my_patient = await patient_service.get_patient_by_user(current_user.id)
                if not my_patient or my_patient.id != patient.id:
                    raise HTTPException(status_code=403, detail="Not authorized")

        response = await ai_chat_service.chat(
            message=request.message,
            conversation_history=request.conversation_history,
            patient=patient,
            context=request.context,
        )

        return APIResponse.success_response(
            data=ChatMessageResponse(
                message=response.message,
                tool_calls=response.tool_calls,
                thinking=response.thinking,
                citations=response.citations,
            ),
        )
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise open_care_exception_to_http(e)
        raise


@router.post("/chat/stream")
async def chat_with_ai_stream(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Stream chat with AI assistant (Server-Sent Events)."""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    async def generate():
        try:
            patient = None
            if request.patient_id:
                from app.services.patient import patient_service
                patient = await patient_service.get_patient(request.patient_id)

            response = await ai_chat_service.chat(
                message=request.message,
                conversation_history=request.conversation_history,
                patient=patient,
                context=request.context,
            )

            # Simulate streaming
            words = response.message.split()
            for i, word in enumerate(words):
                chunk = {
                    "type": "content",
                    "content": word + " ",
                    "done": i == len(words) - 1,
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.02)  # Simulate typing delay

            # Send tool calls if any
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool_call': tool_call})}\n\n"

            # Send done signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/conversation-history/{patient_id}", response_model=APIResponse[List[dict]])
async def get_conversation_history(
    patient_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
):
    """Get AI conversation history for a patient."""
    # Check permissions
    if current_user.is_patient:
        from app.services.patient import patient_service
        my_patient = await patient_service.get_patient_by_user(current_user.id)
        if not my_patient or my_patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")

    # TODO: Implement conversation history storage and retrieval
    return APIResponse.success_response(data=[], message="Not yet implemented")


# --- AI Tool Definitions for Hermes Integration ---

@router.get("/tools", response_model=APIResponse[List[dict]])
async def get_ai_tools(
    current_user: User = Depends(get_current_active_user),
):
    """Get available AI tool definitions for Hermes integration."""
    tools = [
        {
            "name": "check_drug_interaction",
            "description": "Check interaction between two medications",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_a": {"type": "string", "description": "First medication name"},
                    "drug_b": {"type": "string", "description": "Second medication name"},
                    "patient_id": {"type": "string", "format": "uuid", "description": "Optional patient ID"},
                },
                "required": ["drug_a", "drug_b"],
            },
        },
        {
            "name": "check_multiple_drug_interactions",
            "description": "Check interactions among multiple medications",
            "parameters": {
                "type": "object",
                "properties": {
                    "medications": {"type": "array", "items": {"type": "string"}, "minItems": 2},
                    "patient_id": {"type": "string", "format": "uuid", "description": "Optional patient ID"},
                },
                "required": ["medications"],
            },
        },
        {
            "name": "get_patient_summary",
            "description": "Generate AI summary of patient medical history",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "format": "uuid"},
                },
                "required": ["patient_id"],
            },
        },
        {
            "name": "get_medical_recommendations",
            "description": "Get AI medical recommendations for an encounter",
            "parameters": {
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "format": "uuid"},
                    "context": {"type": "object", "description": "Additional context"},
                },
                "required": ["encounter_id"],
            },
        },
        {
            "name": "book_appointment",
            "description": "Book an appointment for a patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "format": "uuid"},
                    "doctor_id": {"type": "string", "format": "uuid"},
                    "scheduled_at": {"type": "string", "format": "date-time"},
                    "duration_minutes": {"type": "integer", "default": 30},
                    "chief_complaint": {"type": "string"},
                },
                "required": ["patient_id", "doctor_id", "scheduled_at"],
            },
        },
        {
            "name": "get_patient_medications",
            "description": "Get patient's current medications",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "format": "uuid"},
                },
                "required": ["patient_id"],
            },
        },
        {
            "name": "get_patient_reports",
            "description": "Get patient's recent medical reports",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "format": "uuid"},
                    "document_type": {"type": "string"},
                },
                "required": ["patient_id"],
            },
        },
        {
            "name": "get_upcoming_appointments",
            "description": "Get patient's upcoming appointments",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "format": "uuid"},
                },
                "required": ["patient_id"],
            },
        },
    ]

    return APIResponse.success_response(data=tools)