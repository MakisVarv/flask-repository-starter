from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.permissions.model import Permission


class PermissionRepository(BaseRepository[Permission]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, Permission)

    def get_by_name(self, name: str) -> Permission | None:

        stmt = select(Permission).where(Permission.name == name)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, name: str) -> bool:

        return self.get_by_name(name) is not None

    def update(self, permission: Permission, data: dict[str, Any]) -> Permission:
        if "name" in data:
            permission.name = data["name"]

        if "description" in data:
            permission.description = data["description"]

        self.session.flush()
        self.session.refresh(permission)

        return permission
