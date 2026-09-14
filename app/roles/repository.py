import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.roles.model import Role


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Role)

    def get_by_name(self, name: str) -> Role | None:

        stmt = select(Role).where(Role.name == name)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, name: str) -> bool:

        return self.get_by_name(name) is not None

    def update(self, role: Role, data: dict[str, Any]) -> Role:
        if "name" in data:
            role.name = data["name"]

        if "description" in data:
            role.description = data["description"]

        if "level" in data:
            role.level = data["level"]

        self.session.flush()
        self.session.refresh(role)

        return role
