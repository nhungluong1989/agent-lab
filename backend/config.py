from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vn_banking.db"

    # Groq
    GROQ_API_KEY: str = ""

    # Email (Resend API — https://resend.com, free tier 3k emails/month)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "VN Real Estate <onboarding@resend.dev>"

    # Gmail (legacy — not used on cloud deployments, SMTP is blocked by Render)
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""

    # Schedules
    CRAWL_SCHEDULE_HOUR: int = 7
    CRAWL_SCHEDULE_MINUTE: int = 0
    NOTIFY_SCHEDULE_HOUR: int = 8
    NOTIFY_SCHEDULE_MINUTE: int = 0

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ("backend/.env", ".env")


settings = Settings()
