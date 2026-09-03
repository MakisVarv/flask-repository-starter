import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.associations import role_permissions
from app.config.database import Base
from app.config.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.permissions.model import Permission
    from app.users.model import User


class Role(TimestampMixin, Base):

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
    )
