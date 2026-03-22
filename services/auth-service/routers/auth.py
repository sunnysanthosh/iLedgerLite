from db import get_db
from fastapi import APIRouter, Depends, status
from models.org import OrgMembership
from models.user import User
from redis.asyncio import Redis
from schemas.auth import LoginRequest, OrgRef, RefreshRequest, RegisterRequest, TokenResponse, UserProfile
from services.auth_service import authenticate_user, get_current_user, refresh_tokens, register_user
from services.redis_client import get_redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(data, db)
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        organisations=[],  # freshly created — caller can fetch /me after login for full orgs
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return await authenticate_user(data.email, data.password, db, redis_client)


@router.get("/me", response_model=UserProfile)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OrgMembership)
        .options(selectinload(OrgMembership.organisation))
        .where(OrgMembership.user_id == current_user.id, OrgMembership.is_active.is_(True))
        .execution_options(populate_existing=True)
    )
    memberships = result.scalars().all()

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        organisations=[
            OrgRef(
                id=str(m.org_id),
                name=m.organisation.name,
                role=m.role,
                is_personal=m.organisation.is_personal,
            )
            for m in memberships
        ],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return await refresh_tokens(data.refresh_token, db, redis_client)
