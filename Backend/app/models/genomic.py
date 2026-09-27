import uuid
from datetime import date
from sqlalchemy import Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class BiomarkerGenomicRecord(Base):
    __tablename__ = "biomarker_genomic_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    gene_symbol = Column(String(64), nullable=False, index=True)  # e.g. CYP2C19, HLA-B, CYP2D6
    variant_allele = Column(String(100), nullable=False)  # e.g. *2/*2, *57:01 (Positive)
    phenotype = Column(String(100), nullable=False)  # e.g. Poor Metabolizer, Hypersensitivity Risk
    test_date = Column(Date, default=date.today, nullable=False)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="genomic_records")
    verified_by = relationship("User", back_populates="verified_genomics")
