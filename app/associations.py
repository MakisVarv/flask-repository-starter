from sqlalchemy import Column, ForeignKey, Table, Uuid

from app.config.database import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        Uuid(),
        ForeignKey("roles.id"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Uuid(),
        ForeignKey("permissions.id"),
        primary_key=True,
    ),
)
