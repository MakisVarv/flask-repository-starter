import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = os.getenv("TEST_DATABASE_URL")
