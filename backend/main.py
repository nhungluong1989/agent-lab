import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.database import init_db
from backend.crawlers.scheduler import run_crawl_all, ensure_districts_exist
from backend.database.database import AsyncSessionLocal
from backend.api import auth, chat, notifications
from backend.api import analytics, listings
from backend.services.notification_service import send_daily_notifications

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await ensure_districts_exist(db)

    await run_crawl_all()

    scheduler.add_job(
        run_crawl_all,
        CronTrigger(hour=settings.CRAWL_SCHEDULE_HOUR, minute=settings.CRAWL_SCHEDULE_MINUTE),
        id="daily_crawl",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_notifications,
        CronTrigger(hour=settings.NOTIFY_SCHEDULE_HOUR, minute=settings.NOTIFY_SCHEDULE_MINUTE),
        id="daily_notifications",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="VN Real Estate Intelligence API",
    description="Vietnam real estate investment analytics platform",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(listings.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
