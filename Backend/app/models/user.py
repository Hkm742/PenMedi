import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class UserRole(str, enum.Enum):
    Administrator = "Administrator"
    Clinician = "Clinician"
    Lab_Officer = "Lab_Officer"
    Auditor = "Auditor"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role_enum", native_enum=False), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    diagnoses = relationship("ClinicalDiagnosis", back_populates="clinician")
    verified_genomics = relationship("BiomarkerGenomicRecord", back_populates="verified_by")
    acknowledged_alerts = relationship("AlertInstance", back_populates="acknowledged_by")
    audit_logs = relationship("AuditLog", back_populates="actor")
