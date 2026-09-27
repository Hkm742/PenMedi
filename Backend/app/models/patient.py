import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Column, Date, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    medical_record_number = Column(String(64), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    sex = Column(String(16), nullable=False)  # 'M', 'F', 'Other'
    contact_info = Column(JSON, nullable=True)  # {phone, address, emergency_contact}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    diagnoses = relationship("ClinicalDiagnosis", back_populates="patient", cascade="all, delete-orphan", order_by="desc(ClinicalDiagnosis.date_diagnosed)")
    medications = relationship("MedicationHistory", back_populates="patient", cascade="all, delete-orphan", order_by="desc(MedicationHistory.start_date)")
    genomic_records = relationship("BiomarkerGenomicRecord", back_populates="patient", cascade="all, delete-orphan", order_by="desc(BiomarkerGenomicRecord.test_date)")
    alerts = relationship("AlertInstance", back_populates="patient", cascade="all, delete-orphan", order_by="desc(AlertInstance.triggered_at)")
