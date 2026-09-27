from datetime import date, datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from app.schemas.clinical import ClinicalDiagnosisOut, MedicationHistoryOut
from app.schemas.genomic import BiomarkerGenomicRecordOut
from app.schemas.cdss import AlertInstanceOut


class PatientBase(BaseModel):
    medical_record_number: str = Field(..., max_length=64, description="E.g. LMTH-2024-0012")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    dob: date
    sex: str = Field(..., description="'M', 'F', or 'Other'")
    contact_info: Optional[Dict[str, Any]] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[date] = None
    sex: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None


class PatientOut(PatientBase):
    id: uuid.UUID
    created_at: datetime
    active_alerts_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PatientDetailOut(PatientOut):
    diagnoses: List[ClinicalDiagnosisOut] = []
    medications: List[MedicationHistoryOut] = []
    genomic_records: List[BiomarkerGenomicRecordOut] = []
    alerts: List[AlertInstanceOut] = []

    class Config:
        from_attributes = True
