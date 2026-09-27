from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_client_ip, get_db, require_role
from app.models.medication import MedicationHistory
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.clinical import (
    ClinicalDiagnosisCreate, ClinicalDiagnosisOut,
    MedicationHistoryCreate, MedicationHistoryOut, MedicationHistoryUpdate
)
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService

router = APIRouter(tags=["Clinical Observations & Medications"])


@router.post(
    "/patients/{patient_id}/diagnoses",
    response_model=ClinicalDiagnosisOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_clinical_diagnosis(
    patient_id: uuid.UUID,
    diag_in: ClinicalDiagnosisCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """Clinician-only: Record a verified clinical diagnosis for a patient."""
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    ip_address = get_client_ip(request)
    diagnosis = await PatientService.add_diagnosis(
        db=db,
        patient_id=patient_id,
        data=diag_in,
        clinician_id=current_clinician.id,
        ip_address=ip_address,
    )
    return diagnosis


@router.post(
    "/patients/{patient_id}/medications",
    response_model=MedicationHistoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_medication_history(
    patient_id: uuid.UUID,
    med_in: MedicationHistoryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """Clinician-only: Record a medication prescription. Triggers automatic CDSS pharmacogenomic check."""
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    ip_address = get_client_ip(request)
    medication = await PatientService.add_medication(
        db=db,
        patient_id=patient_id,
        data=med_in,
        actor_id=current_clinician.id,
        ip_address=ip_address,
    )
    return medication


@router.patch(
    "/patients/{patient_id}/medications/{medication_id}",
    response_model=MedicationHistoryOut,
)
async def update_medication_history(
    patient_id: uuid.UUID,
    medication_id: uuid.UUID,
    med_update: MedicationHistoryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_clinician: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """Clinician-only: Update medication dosage, active status, or end date."""
    query = select(MedicationHistory).where(
        MedicationHistory.id == medication_id,
        MedicationHistory.patient_id == patient_id,
    )
    res = await db.execute(query)
    med = res.scalar_one_or_none()

    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication record not found")

    if med_update.dosage is not None:
        med.dosage = med_update.dosage
    if med_update.frequency is not None:
        med.frequency = med_update.frequency
    if med_update.end_date is not None:
        med.end_date = med_update.end_date
    if med_update.active is not None:
        med.active = med_update.active

    await db.commit()
    await db.refresh(med)

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_clinician.id,
        action="MEDICATION_UPDATE",
        resource="medication",
        resource_id=str(med.id),
        ip_address=ip_address,
        details={"active": med.active, "dosage": med.dosage},
    )

    return med
