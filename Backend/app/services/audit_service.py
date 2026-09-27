import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.user import User


class AuditService:
    @staticmethod
    def calculate_payload_hash(data: Any) -> str:
        """Calculate immutable SHA-256 hash of event payload."""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    async def log_event(
        cls,
        db: AsyncSession,
        action: str,
        resource: str,
        actor_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create an immutable audit log record."""
        payload_hash = cls.calculate_payload_hash(
            {
                "action": action,
                "resource": resource,
                "actor_id": str(actor_id) if actor_id else None,
                "resource_id": resource_id,
                "details": details or {},
            }
        )

        audit_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
            payload_hash=payload_hash,
            details=details or {},
        )
        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry

    @classmethod
    async def get_logs(
        cls,
        db: AsyncSession,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query audit logs with actor information and count."""
        query = select(AuditLog, User.email, User.full_name).outerjoin(User, AuditLog.actor_id == User.id)

        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)

        # Count total
        count_query = select(func.count(AuditLog.id))
        if action:
            count_query = count_query.where(AuditLog.action == action)
        if resource:
            count_query = count_query.where(AuditLog.resource == resource)
        if actor_id:
            count_query = count_query.where(AuditLog.actor_id == actor_id)
        if start_date:
            count_query = count_query.where(AuditLog.timestamp >= start_date)
        if end_date:
            count_query = count_query.where(AuditLog.timestamp <= end_date)

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        query = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit)
        results = await db.execute(query)

        logs = []
        for log, email, full_name in results.all():
            logs.append({
                "id": log.id,
                "actor_id": log.actor_id,
                "actor_email": email,
                "actor_name": full_name,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp,
                "payload_hash": log.payload_hash,
                "details": log.details,
            })

        return logs, total

    @classmethod
    async def get_stats(cls, db: AsyncSession) -> Dict[str, Any]:
        """Aggregate audit statistics for auditing and system monitoring."""
        total_res = await db.execute(select(func.count(AuditLog.id)))
        total_logs = total_res.scalar_one()

        # Breakdown by action
        action_res = await db.execute(
            select(AuditLog.action, func.count(AuditLog.id)).group_by(AuditLog.action)
        )
        actions_breakdown = {row[0]: row[1] for row in action_res.all()}

        # Breakdown by resource
        resource_res = await db.execute(
            select(AuditLog.resource, func.count(AuditLog.id)).group_by(AuditLog.resource)
        )
        resources_breakdown = {row[0]: row[1] for row in resource_res.all()}

        # 24h count
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_res = await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.timestamp >= cutoff_24h)
        )
        recent_activity_count_24h = recent_res.scalar_one()

        return {
            "total_logs": total_logs,
            "actions_breakdown": actions_breakdown,
            "resources_breakdown": resources_breakdown,
            "recent_activity_count_24h": recent_activity_count_24h,
        }
