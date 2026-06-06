from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.api.auth import get_current_user
from backend.database.database import get_db
from backend.database.models import User, NotificationLog
from backend.services.notification_service import send_daily_notifications
from backend.services.ai_service import generate_daily_summary
from backend.services.email_service import send_email, build_notification_html

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="No email address on your account")
    if not current_user.email_notifications:
        raise HTTPException(status_code=400, detail="Email notifications are disabled in your settings")

    try:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        summary = await generate_daily_summary(current_user.role, db)
        subject = f"[{current_user.role.capitalize()}] VN Real Estate Daily Insight — {date_str}"
        html = build_notification_html(current_user.username, current_user.role, summary, date_str)
        success = await send_email(current_user.email, subject, html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")

    status = "sent" if success else "failed"
    db.add(NotificationLog(
        user_id=current_user.id, channel="email", status=status,
        subject=subject, message=summary,
    ))
    await db.commit()

    if not success:
        raise HTTPException(status_code=500, detail="SMTP send failed — check GMAIL_USER and GMAIL_APP_PASSWORD in server environment variables")

    return {"message": f"Test email sent to {current_user.email}"}


@router.post("/send-all")
async def trigger_all_notifications(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_daily_notifications)
    return {"message": "Daily notifications triggered"}
