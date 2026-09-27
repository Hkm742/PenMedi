import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    payload_hash = Column(String(64), nullable=False)  # SHA-256 immutable digest
    details = Column(JSON, nullable=True)

    # Relationships
    actor = relationship("User", back_populates="audit_logs")
