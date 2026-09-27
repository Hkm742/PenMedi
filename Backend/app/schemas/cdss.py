from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from app.models.cdss import AlertSeverity, AlertStatus


class CDSSRuleBase(BaseModel):
    rule_code: str = Field(..., max_length=100)
    description: str
    condition_expression: Dict[str, Any]
    severity: AlertSeverity
    recommendation: str
    clinical_reference: str


class CDSSRuleCreate(CDSSRuleBase):
    pass


class CDSSRuleOut(CDSSRuleBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    clinician_note: str = Field(..., min_length=3, description="Clinical justification or acknowledgment note")
    override: bool = Field(False, description="Set True if clinician chooses to override recommendation")


class AlertInstanceOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    rule_id: uuid.UUID
    severity: AlertSeverity
    message: str
    evidence_data: Optional[Dict[str, Any]] = None
    triggered_at: datetime
    acknowledged_by_id: Optional[uuid.UUID] = None
    acknowledged_at: Optional[datetime] = None
    clinician_note: Optional[str] = None
    status: AlertStatus
    rule: Optional[CDSSRuleOut] = None

    class Config:
        from_attributes = True


class CDSSEvaluationResult(BaseModel):
    patient_id: uuid.UUID
    evaluated_at: datetime
    evaluated_medications_count: int
    evaluated_biomarkers_count: int
    alerts_triggered_count: int
    alerts: List[AlertInstanceOut]
    disclaimer: str = (
        "Strict decision-support guidance only for qualified clinicians. "
        "Does not autonomously diagnose or prescribe. Final clinical judgment rests with the treating clinician."
    )
