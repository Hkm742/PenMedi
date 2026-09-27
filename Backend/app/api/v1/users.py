from typing import Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_client_ip, get_db, require_role
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.Administrator)),
) -> Any:
    """Administrator-only: List all institutional users and their role assignments."""
    query = select(User).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.Administrator)),
) -> Any:
    """Administrator-only: Provision a new clinical, lab, or auditor user account."""
    # Check email duplicate
    query = select(User).where(User.email == user_in.email.lower().strip())
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_in.email}' already exists.",
        )

    user = User(
        email=user_in.email.lower().strip(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=user_in.role,
        is_active=user_in.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_admin.id,
        action="USER_PROVISION",
        resource="user",
        resource_id=str(user.id),
        ip_address=ip_address,
        details={"created_email": user.email, "assigned_role": user.role.value},
    )

    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.Administrator)),
) -> Any:
    """Administrator-only: Update user details, role assignment, or active status."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_in.full_name is not None:
        user.full_name = user_in.full_name.strip()
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)

    await db.commit()
    await db.refresh(user)

    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_admin.id,
        action="USER_UPDATE",
        resource="user",
        resource_id=str(user.id),
        ip_address=ip_address,
        details={"email": user.email, "role": user.role.value, "is_active": user.is_active},
    )

    return user
