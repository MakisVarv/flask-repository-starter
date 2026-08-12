from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SessionLocal = sessionmaker()


class Base(DeclarativeBase):
    pass


def init_db(app):
    database_url = app.config["DATABASE_URL"]

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    engine = create_engine(database_url)

    SessionLocal.configure(bind=engine)
