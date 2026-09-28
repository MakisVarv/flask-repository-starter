import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=180)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_ERROR_MESSAGE_KEY = "message"

    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_REFRESH_COOKIE_PATH = "/api/auth"

    MAIL_HOST = os.getenv("MAIL_HOST", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )
    RATELIMIT_HEADERS_ENABLED = True


class DevelopmentConfig(Config):
    JWT_COOKIE_SECURE = False


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL: str | None = os.getenv("TEST_DATABASE_URL")
    JWT_COOKIE_SECURE = False
    RATELIMIT_STORAGE_URI = "memory://"
