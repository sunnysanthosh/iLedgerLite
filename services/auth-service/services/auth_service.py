import uuid

from config import settings
from db import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.user import User
from redis.asyncio import Redis
from schemas.auth import RegisterRequest, TokenResponse
from services.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer(auto_error=False)

INVALID_CREDENTIALS = "Invalid email or password"


async def register_user(data: RegisterRequest, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalars().first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession, redis_client: Redis) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated")

    access_token = create_access_token(str(user.id))
    refresh_token, jti = create_refresh_token(str(user.id))

    ttl = settings.refresh_token_expire_days * 86400
    await redis_client.setex(f"refresh:{jti}", ttl, str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_tokens(refresh_token_str: str, db: AsyncSession, redis_client: Redis) -> TokenResponse:
    payload = decode_refresh_token(refresh_token_str)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    jti = payload["jti"]
    user_id = await redis_client.get(f"refresh:{jti}")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or already used")

    # Single-use: delete old token
    await redis_client.delete(f"refresh:{jti}")

    # Issue new pair
    access_token = create_access_token(user_id)
    new_refresh_token, new_jti = create_refresh_token(user_id)

    ttl = settings.refresh_token_expire_days * 86400
    await redis_client.setex(f"refresh:{new_jti}", ttl, user_id)

    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
