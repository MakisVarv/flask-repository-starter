import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY: str | None = os.getenv("JWT_SECRET_KEY")


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL: str | None = os.getenv("TEST_DATABASE_URL")
