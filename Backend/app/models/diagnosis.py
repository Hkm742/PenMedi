import uuid
from datetime import date
from sqlalchemy import Column, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class ClinicalDiagnosis(Base):
    __tablename__ = "clinical_diagnoses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    icd10_code = Column(String(32), nullable=False, index=True)
    description = Column(Text, nullable=False)
    date_diagnosed = Column(Date, default=date.today, nullable=False)
    clinician_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")
    clinician = relationship("User", back_populates="diagnoses")
