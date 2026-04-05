import uuid

from config import settings
from db import get_db
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from models.org import Organisation, OrgMembership
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

bearer_scheme = HTTPBearer(auto_error=False)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


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
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id)).execution_options(populate_existing=True)
    )
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is deactivated")

    return user


async def get_org_member(
    x_org_id: str | None = Header(None, alias="X-Org-ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrgMembership:
    q = (
        select(OrgMembership)
        .options(selectinload(OrgMembership.organisation))
        .where(OrgMembership.user_id == current_user.id, OrgMembership.is_active.is_(True))
    )
    if x_org_id:
        try:
            org_uuid = uuid.UUID(x_org_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Org-ID format")
        q = q.where(OrgMembership.org_id == org_uuid)
    else:
        q = q.join(Organisation, OrgMembership.org_id == Organisation.id).where(Organisation.is_personal.is_(True))
    result = await db.execute(q.execution_options(populate_existing=True))
    membership = result.scalars().first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organisation")
    return membership


async def get_write_member(
    membership: OrgMembership = Depends(get_org_member),
) -> OrgMembership:
    """Like get_org_member but rejects read_only members on mutating endpoints."""
    if membership.role == "read_only":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Read-only members cannot perform this action"
        )
    return membership
