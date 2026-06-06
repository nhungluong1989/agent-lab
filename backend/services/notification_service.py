import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.database import AsyncSessionLocal
from backend.database.models import User, NotificationLog
from backend.services.ai_service import generate_daily_summary
from backend.services.email_service import send_email, build_notification_html

logger = logging.getLogger(__name__)


async def send_daily_notifications():
    """Send personalized daily summaries to all active users."""
    logger.info("Starting daily notification job...")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()

        for user in users:
            if not user.email_notifications:
                continue
            try:
                summary = await generate_daily_summary(user.role, db)
                await _notify_user(user, summary, date_str, db)
            except Exception as e:
                logger.error(f"Notification failed for user {user.id}: {e}")

    logger.info("Daily notification job completed.")


async def _notify_user(user: User, summary: str, date_str: str, db: AsyncSession):
    if user.email_notifications and user.email:
        subject = f"[{user.role.capitalize()}] VN Real Estate Daily Insight — {date_str}"
        html = build_notification_html(user.username, user.role, summary, date_str)
        status = "sent" if await send_email(user.email, subject, html) else "failed"
        db.add(NotificationLog(
            user_id=user.id, channel="email", status=status,
            subject=subject, message=summary,
        ))

    user.last_notified_at = datetime.utcnow()
    await db.commit()
