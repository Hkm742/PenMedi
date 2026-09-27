from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    actor_name: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    payload_hash: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AuditFilterParams(BaseModel):
    action: Optional[str] = None
    resource: Optional[str] = None
    actor_id: Optional[uuid.UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


class AuditStatsOut(BaseModel):
    total_logs: int
    actions_breakdown: Dict[str, int]
    resources_breakdown: Dict[str, int]
    recent_activity_count_24h: int
