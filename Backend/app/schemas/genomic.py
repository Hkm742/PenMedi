from datetime import date
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class BiomarkerGenomicRecordBase(BaseModel):
    gene_symbol: str = Field(..., max_length=64, description="E.g. CYP2C19, HLA-B, CYP2D6, TPMT")
    variant_allele: str = Field(..., max_length=100, description="E.g. *2/*2, *57:01 (Positive)")
    phenotype: str = Field(..., max_length=100, description="E.g. Poor Metabolizer, Hypersensitivity Risk")
    test_date: date = Field(default_factory=date.today)


class BiomarkerGenomicRecordCreate(BiomarkerGenomicRecordBase):
    pass


class BiomarkerGenomicRecordOut(BiomarkerGenomicRecordBase):
    id: uuid.UUID
    patient_id: uuid.UUID
    verified_by_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
