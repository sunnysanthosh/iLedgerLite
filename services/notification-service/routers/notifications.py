import uuid

from db import get_db
from fastapi import APIRouter, Depends, Query
from models.org import OrgMembership
from models.user import User
from schemas.notification import (
    InternalNotificationCreate,
    MarkReadResponse,
    NotificationList,
    NotificationResponse,
    ReminderRequest,
)
from services.notification_service import create_reminder, create_system_notification, list_notifications, mark_as_read
from services.security import get_current_user, get_org_member, get_write_member
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    membership: OrgMembership = Depends(get_org_member),
    db: AsyncSession = Depends(get_db),
):
    notifications, total, unread_count = await list_notifications(
        membership.org_id,
        db,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
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
    membership: OrgMembership = Depends(get_write_member),
    db: AsyncSession = Depends(get_db),
):
    return await create_reminder(membership.user_id, membership.org_id, data.customer_id, data.message, db)


@router.post("/internal", response_model=NotificationResponse, status_code=201, include_in_schema=False)
async def internal_notify_endpoint(
    data: InternalNotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Internal endpoint for service-to-service notifications (no auth required)."""
    return await create_system_notification(
        user_id=data.user_id,
        org_id=data.org_id,
        title=data.title,
        message=data.message,
        notification_type=data.type,
        related_entity_id=data.related_entity_id,
        db=db,
    )
