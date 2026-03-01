from db import get_db
from fastapi import APIRouter, Depends, status
from models.user import User
from schemas.user import (
    OnboardingRequest,
    SettingsUpdate,
    UserProfile,
    UserSettingsResponse,
    UserUpdate,
)
from services.security import get_current_user
from services.user_service import (
    complete_onboarding,
    deactivate_user,
    update_user_profile,
    update_user_settings,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserProfile)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_user_profile(current_user, data, db)


@router.post("/me/onboarding", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def onboarding(
    data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await complete_onboarding(current_user, data, db)


@router.put("/me/settings", response_model=UserSettingsResponse)
async def settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await update_user_settings(current_user, data, db)
    return user.settings


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await deactivate_user(current_user, db)
    return {"detail": "Account deactivated"}
