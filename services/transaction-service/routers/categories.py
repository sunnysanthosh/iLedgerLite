from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from schemas.category import CategoryCreate, CategoryResponse
from services.category_service import create_category, list_categories
from services.security import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_category(current_user.id, data, db)


@router.get("", response_model=list[CategoryResponse])
async def list_all(
    type: str | None = Query(None, description="Filter by 'income' or 'expense'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_categories(current_user.id, db, category_type=type)
