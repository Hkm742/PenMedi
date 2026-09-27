import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFORMATIONAL = "INFORMATIONAL"


class AlertStatus(str, enum.Enum):
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    OVERRIDDEN = "OVERRIDDEN"


class CDSSRule(Base):
    __tablename__ = "cdss_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    # Structured condition: e.g. {"drug": "Clopidogrel", "gene": "CYP2C19", "phenotypes": ["Poor Metabolizer", "Intermediate Metabolizer"]}
    condition_expression = Column(JSON, nullable=False)
    severity = Column(Enum(AlertSeverity, name="alert_severity_enum", native_enum=False), nullable=False)
    recommendation = Column(Text, nullable=False)
    clinical_reference = Column(Text, nullable=False)

    # Relationships
    alerts = relationship("AlertInstance", back_populates="rule", cascade="all, delete-orphan")


class AlertInstance(Base):
    __tablename__ = "alert_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("cdss_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity, name="alert_severity_enum", native_enum=False), nullable=False)
    message = Column(Text, nullable=False)
    evidence_data = Column(JSON, nullable=True)  # Snapshot of triggered values: drug, gene, alleles, etc.
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    acknowledged_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    clinician_note = Column(Text, nullable=True)
    status = Column(Enum(AlertStatus, name="alert_status_enum", native_enum=False), default=AlertStatus.TRIGGERED, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="alerts")
    rule = relationship("CDSSRule", back_populates="alerts")
    acknowledged_by = relationship("User", back_populates="acknowledged_alerts")
