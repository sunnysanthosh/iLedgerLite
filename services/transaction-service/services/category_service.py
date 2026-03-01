import uuid

from fastapi import HTTPException, status
from models.category import Category
from schemas.category import CategoryCreate
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_category(user_id: uuid.UUID, data: CategoryCreate, db: AsyncSession) -> Category:
    category = Category(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        type=data.type,
        icon=data.icon,
        is_system=False,
    )
    db.add(category)
    await db.flush()
    result = await db.execute(
        select(Category).where(Category.id == category.id).execution_options(populate_existing=True)
    )
    return result.scalars().first()


async def list_categories(
    user_id: uuid.UUID,
    db: AsyncSession,
    category_type: str | None = None,
) -> list[Category]:
    query = select(Category).where(or_(Category.user_id == user_id, Category.is_system.is_(True)))
    if category_type is not None:
        query = query.where(Category.type == category_type)
    query = query.order_by(Category.is_system.desc(), Category.name)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_category(category_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Category:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            or_(Category.user_id == user_id, Category.is_system.is_(True)),
        )
    )
    category = result.scalars().first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
