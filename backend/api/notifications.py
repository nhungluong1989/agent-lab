from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.api.auth import get_current_user
from backend.database.database import get_db
from backend.database.models import User, NotificationLog
from backend.services.notification_service import send_daily_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationLogOut(BaseModel):
    id: int
    channel: str
    status: str
    subject: Optional[str]
    sent_at: datetime

    class Config:
        from_attributes = True


@router.get("/logs", response_model=List[NotificationLogOut])
async def get_notification_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == current_user.id)
        .order_by(desc(NotificationLog.sent_at))
        .limit(20)
    )
    return result.scalars().all()


@router.post("/test")
async def send_test_notification(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """Trigger a test notification for the current user."""
    background_tasks.add_task(send_daily_notifications)
    return {"message": "Test notification triggered"}


@router.post("/send-all")
async def trigger_all_notifications(background_tasks: BackgroundTasks):
    """Manually trigger daily notifications for all users."""
    background_tasks.add_task(send_daily_notifications)
    return {"message": "Daily notifications triggered"}
