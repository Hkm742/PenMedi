from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_client_ip, get_current_user, get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user import User
from app.schemas.user import LoginRequest, RefreshTokenRequest, Token, UserOut
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate clinician or healthcare officer and issue JWT access and refresh tokens."""
    query = select(User).where(User.email == credentials.email.lower().strip())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    ip_address = get_client_ip(request)

    if not user or not verify_password(credentials.password, user.hashed_password):
        # Audit log failed login attempt
        await AuditService.log_event(
            db=db,
            action="LOGIN_FAILED",
            resource="auth",
            resource_id=credentials.email,
            ip_address=ip_address,
            details={"email": credentials.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Please contact your system administrator.",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        full_name=user.full_name,
        scopes=[user.role.value],
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        role=user.role.value,
    )

    # Audit log successful login
    await AuditService.log_event(
        db=db,
        actor_id=user.id,
        action="USER_LOGIN",
        resource="auth",
        resource_id=str(user.id),
        ip_address=ip_address,
        details={"role": user.role.value, "email": user.email},
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    payload_in: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Exchange a valid refresh token for a fresh access token pair."""
    try:
        decoded = decode_token(payload_in.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh endpoint",
            )
        user_id_str = decoded.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or invalid",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        full_name=user.full_name,
        scopes=[user.role.value],
    )
    new_refresh_token = create_refresh_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieve details for current authenticated session."""
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Audit log clinical user logout event."""
    ip_address = get_client_ip(request)
    await AuditService.log_event(
        db=db,
        actor_id=current_user.id,
        action="USER_LOGOUT",
        resource="auth",
        resource_id=str(current_user.id),
        ip_address=ip_address,
        details={"email": current_user.email},
    )
    return {"message": "Session terminated successfully"}
