import uuid

from fastapi import HTTPException, status
from models.user import User
from models.user_settings import UserSettings
from schemas.user import OnboardingRequest, SettingsUpdate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def _reload_user(user_id: uuid.UUID, db: AsyncSession) -> User:
    """Re-query user with settings eagerly loaded (avoids lazy-load in async)."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.settings))
        .where(User.id == user_id)
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def get_user_profile(user_id: uuid.UUID, db: AsyncSession) -> User:
    user = await _reload_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def update_user_profile(user: User, data: UserUpdate, db: AsyncSession) -> User:
    if data.email is not None and data.email != user.email:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalars().first() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        user.email = data.email

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone

    await db.flush()
    return await _reload_user(user.id, db)


async def complete_onboarding(user: User, data: OnboardingRequest, db: AsyncSession) -> User:
    if user.settings is not None and user.settings.onboarding_completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Onboarding already completed")

    if user.settings is None:
        user_settings = UserSettings(
            id=uuid.uuid4(),
            user_id=user.id,
            account_type=data.account_type,
            currency=data.currency,
            language=data.language,
            business_category=data.business_category,
            onboarding_completed=True,
        )
        db.add(user_settings)
    else:
        user.settings.account_type = data.account_type
        user.settings.currency = data.currency
        user.settings.language = data.language
        user.settings.business_category = data.business_category
        user.settings.onboarding_completed = True

    await db.flush()
    return await _reload_user(user.id, db)


async def update_user_settings(user: User, data: SettingsUpdate, db: AsyncSession) -> User:
    if user.settings is None:
        user_settings = UserSettings(id=uuid.uuid4(), user_id=user.id)
        db.add(user_settings)
        await db.flush()

    # Re-load to get the newly created settings
    user = await _reload_user(user.id, db)

    if data.notifications_enabled is not None:
        user.settings.notifications_enabled = data.notifications_enabled
    if data.language is not None:
        user.settings.language = data.language
    if data.currency is not None:
        user.settings.currency = data.currency

    await db.flush()
    return await _reload_user(user.id, db)


async def deactivate_user(user: User, db: AsyncSession) -> User:
    user.is_active = False
    await db.flush()
    return await _reload_user(user.id, db)
