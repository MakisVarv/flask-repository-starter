import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True

    JWT_REFRESH_COOKIE_PATH = "/api/auth"


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL: str | None = os.getenv("TEST_DATABASE_URL")
