import uuid
from datetime import date
from sqlalchemy import Boolean, Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class MedicationHistory(Base):
    __tablename__ = "medication_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False, index=True)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    start_date = Column(Date, default=date.today, nullable=False)
    end_date = Column(Date, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="medications")
