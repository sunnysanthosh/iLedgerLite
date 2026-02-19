import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models.user import User
from schemas.notification import (
    MarkReadResponse,
    NotificationList,
    NotificationResponse,
    ReminderRequest,
)
from services.notification_service import create_reminder, list_notifications, mark_as_read
from services.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications, total, unread_count = await list_notifications(
        user.id, db, skip=skip, limit=limit, unread_only=unread_only,
    )
    return NotificationList(
        items=notifications,
        total=total,
        skip=skip,
        limit=limit,
        unread_count=unread_count,
    )


@router.put("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_read_endpoint(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notification = await mark_as_read(notification_id, user.id, db)
    return MarkReadResponse(id=notification.id, is_read=notification.is_read)


@router.post("/reminder", response_model=NotificationResponse, status_code=201)
async def send_reminder_endpoint(
    data: ReminderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_reminder(user.id, data.customer_id, data.message, db)
