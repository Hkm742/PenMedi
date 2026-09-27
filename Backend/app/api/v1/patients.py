from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_client_ip, get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientDetailOut, PatientOut
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patient Management"])


@router.get("", response_model=Dict[str, Any])
async def list_patients(
    request: Request,
    search: Optional[str] = Query(None, description="Search by MRN, first or last name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator, UserRole.Lab_Officer)),
) -> Any:
    """Retrieve paginated patient directory with active CDSS alert counts."""
    patients, total = await PatientService.get_patients(
        db=db, search=search, limit=limit, offset=offset
    )

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_user.id,
        action="PATIENT_SEARCH_LIST",
        resource="patient",
        ip_address=ip_address,
        details={"search_query": search, "returned_count": len(patients), "total": total},
    )

    return {
        "items": patients,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: Request,
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator)),
) -> Any:
    """Register a new patient into the PM-CDSS clinical repository."""
    ip_address = get_client_ip(request)
    try:
        patient = await PatientService.create_patient(
            db=db,
            data=patient_in,
            creator_id=current_user.id,
            ip_address=ip_address,
        )
        return patient
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{patient_id}", response_model=PatientDetailOut)
async def get_patient_detail(
    patient_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.Clinician, UserRole.Administrator, UserRole.Lab_Officer)),
) -> Any:
    """Retrieve full aggregated clinical chart including diagnoses, medications, genomic biomarkers, and CDSS alerts."""
    patient = await PatientService.get_patient_detail(db=db, patient_id=patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found")

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_user.id,
        action="PATIENT_CHART_VIEW",
        resource="patient",
        resource_id=str(patient.id),
        ip_address=ip_address,
        details={"mrn": patient.medical_record_number},
    )

    return patient
