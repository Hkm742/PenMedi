from datetime import date
from typing import Optional
import uuid
from pydantic import BaseModel, Field


# Diagnosis Schemas
class ClinicalDiagnosisBase(BaseModel):
    icd10_code: str = Field(..., max_length=32)
    description: str = Field(..., min_length=2)
    date_diagnosed: date = Field(default_factory=date.today)


class ClinicalDiagnosisCreate(ClinicalDiagnosisBase):
    pass


class ClinicalDiagnosisOut(ClinicalDiagnosisBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    clinician_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


# Medication Schemas
class MedicationHistoryBase(BaseModel):
    drug_name: str = Field(..., max_length=255)
    dosage: str = Field(..., max_length=100)
    frequency: str = Field(..., max_length=100)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    active: bool = True


class MedicationHistoryCreate(MedicationHistoryBase):
    pass


class MedicationHistoryUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    end_date: Optional[date] = None
    active: Optional[bool] = None


class MedicationHistoryOut(MedicationHistoryBase):
    id: uuid.UUID
    patient_id: uuid.UUID

    class Config:
        from_attributes = True
