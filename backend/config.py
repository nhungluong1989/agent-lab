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

    # Email (Brevo API — https://brevo.com, free tier 300 emails/day, send to anyone)
    BREVO_API_KEY: str = ""
    EMAIL_FROM_NAME: str = "VN Real Estate Intelligence"
    EMAIL_FROM_ADDRESS: str = ""

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
