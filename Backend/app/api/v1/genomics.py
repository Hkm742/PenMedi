from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_client_ip, get_db, require_role
from app.models.genomic import BiomarkerGenomicRecord
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.genomic import BiomarkerGenomicRecordCreate, BiomarkerGenomicRecordOut
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService

router = APIRouter(tags=["Genomics & Biomarker Laboratory Records"])


@router.post(
    "/patients/{patient_id}/genomics",
    response_model=BiomarkerGenomicRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_genomic_record(
    patient_id: uuid.UUID,
    record_in: BiomarkerGenomicRecordCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_officer: User = Depends(require_role(UserRole.Lab_Officer, UserRole.Administrator)),
) -> Any:
    """Lab Officer: Ingest and verify an authorized laboratory biomarker and genetic test entry."""
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found")

    ip_address = get_client_ip(request)
    record = await PatientService.add_genomic_record(
        db=db,
        patient_id=patient_id,
        data=record_in,
        lab_officer_id=current_officer.id,
        ip_address=ip_address,
    )
    return record


@router.get(
    "/patients/{patient_id}/genomics",
    response_model=List[BiomarkerGenomicRecordOut],
)
async def list_patient_genomic_records(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Lab_Officer, UserRole.Administrator)),
) -> Any:
    """Retrieve all verified genomic biomarker records for a patient."""
    query = (
        select(BiomarkerGenomicRecord)
        .where(BiomarkerGenomicRecord.patient_id == patient_id)
        .order_by(BiomarkerGenomicRecord.test_date.desc())
    )
    res = await db.execute(query)
    return res.scalars().all()


@router.get(
    "/genomics",
    response_model=List[BiomarkerGenomicRecordOut],
)
async def list_all_genomic_records(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Lab_Officer, UserRole.Administrator)),
) -> Any:
    """Lab Officer / Admin: List recent biomarker and genetic test entries across all patients."""
    query = (
        select(BiomarkerGenomicRecord)
        .order_by(BiomarkerGenomicRecord.test_date.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    return res.scalars().all()
