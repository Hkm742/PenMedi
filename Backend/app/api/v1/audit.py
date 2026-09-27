from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_role
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogOut, AuditStatsOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Security & Compliance Audit Trail"])


@router.get("/logs", response_model=Dict[str, Any])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action (e.g. USER_LOGIN, CDSS_EVALUATION)"),
    resource: Optional[str] = Query(None, description="Filter by resource (e.g. patient, alert, user)"),
    actor_id: Optional[uuid.UUID] = Query(None, description="Filter by actor ID"),
    start_date: Optional[datetime] = Query(None, description="Start timestamp filter"),
    end_date: Optional[datetime] = Query(None, description="End timestamp filter"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_auditor: User = Depends(require_role(UserRole.Auditor, UserRole.Administrator)),
) -> Any:
    """
    Auditor & Administrator: Query immutable audit logs with SHA-256 verification hashes.
    Auditors have read-only inspection capability without raw patient medical chart access.
    """
    logs, total = await AuditService.get_logs(
        db=db,
        action=action,
        resource=resource,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return {
        "items": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats", response_model=AuditStatsOut)
async def get_audit_statistics(
    db: AsyncSession = Depends(get_db),
    current_auditor: User = Depends(require_role(UserRole.Auditor, UserRole.Administrator)),
) -> Any:
    """Auditor & Administrator: High-level overview of system security events and resource activity."""
    return await AuditService.get_stats(db=db)
