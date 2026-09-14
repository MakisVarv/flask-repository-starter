import uuid
from datetime import datetime

from flask import Flask
from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

SessionLocal = sessionmaker()


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def init_db(app: Flask) -> None:
    database_url = app.config["DATABASE_URL"]

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    engine = create_engine(database_url)

    SessionLocal.configure(bind=engine)

    app.extensions["db_engine"] = engine
