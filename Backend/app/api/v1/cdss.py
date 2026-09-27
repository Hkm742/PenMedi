from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_client_ip, get_db, require_role
from app.models.cdss import AlertInstance, AlertStatus, CDSSRule
from app.models.user import User, UserRole
from app.schemas.cdss import (
    AlertAcknowledgeRequest, AlertInstanceOut,
    CDSSEvaluationResult, CDSSRuleCreate, CDSSRuleOut
)
from app.services.audit_service import AuditService
from app.services.cdss_engine import CDSSEngine

router = APIRouter(prefix="/cdss", tags=["Clinical Decision Support Engine"])


@router.post("/evaluate/{patient_id}", response_model=CDSSEvaluationResult)
async def evaluate_patient_cdss(
    patient_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """
    Execute deterministic, traceable pharmacogenomic evaluation engine on a patient chart.
    Evaluates active medications against patient's genomic biomarker records and diagnoses.
    """
    ip_address = get_client_ip(request)
    try:
        result = await CDSSEngine.evaluate_patient(
            db=db,
            patient_id=patient_id,
            evaluator_id=current_clinician.id,
            ip_address=ip_address,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/alerts/patient/{patient_id}", response_model=List[AlertInstanceOut])
async def get_patient_alerts(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator, UserRole.Lab_Officer, UserRole.Auditor)),
) -> Any:
    """Retrieve all CDSS alert instances triggered for a patient."""
    query = (
        select(AlertInstance)
        .where(AlertInstance.patient_id == patient_id)
        .options(selectinload(AlertInstance.rule))
        .order_by(AlertInstance.triggered_at.desc())
    )
    res = await db.execute(query)
    return res.scalars().all()


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertInstanceOut)
async def acknowledge_cdss_alert(
    alert_id: uuid.UUID,
    ack_in: AlertAcknowledgeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """
    Clinician Alert Acknowledgment:
    Record explicit review, clinical justification note, and optional therapeutic override.
    """
    ip_address = get_client_ip(request)
    try:
        updated_alert = await CDSSEngine.acknowledge_alert(
            db=db,
            alert_id=alert_id,
            clinician_id=current_clinician.id,
            clinician_note=ack_in.clinician_note,
            override=ack_in.override,
            ip_address=ip_address,
        )
        return updated_alert
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/rules", response_model=List[CDSSRuleOut])
async def list_cdss_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator, UserRole.Lab_Officer, UserRole.Auditor)),
) -> Any:
    """List all registered institutional CDSS pharmacogenomic rules."""
    query = select(CDSSRule).order_by(CDSSRule.rule_code)
    res = await db.execute(query)
    return res.scalars().all()


@router.post("/rules", response_model=CDSSRuleOut, status_code=status.HTTP_201_CREATED)
async def create_cdss_rule(
    rule_in: CDSSRuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.Administrator)),
) -> Any:
    """Administrator-only: Register a new institutional pharmacogenomic decision support rule."""
    # Check duplicate code
    check = await db.execute(select(CDSSRule).where(CDSSRule.rule_code == rule_in.rule_code))
    if check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule with code '{rule_in.rule_code}' already exists.",
        )

    rule = CDSSRule(
        rule_code=rule_in.rule_code.strip(),
        description=rule_in.description.strip(),
        condition_expression=rule_in.condition_expression,
        severity=rule_in.severity,
        recommendation=rule_in.recommendation.strip(),
        clinical_reference=rule_in.clinical_reference.strip(),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_admin.id,
        action="RULE_CREATE",
        resource="rule",
        resource_id=str(rule.id),
        ip_address=ip_address,
        details={"rule_code": rule.rule_code, "severity": rule.severity.value},
    )

    return rule
