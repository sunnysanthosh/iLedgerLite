from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserProfile
from services.auth_service import authenticate_user, get_current_user, refresh_tokens, register_user
from services.redis_client import get_redis

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(data, db)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return await authenticate_user(data.email, data.password, db, redis_client)


@router.get("/me", response_model=UserProfile)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    return await refresh_tokens(data.refresh_token, db, redis_client)
