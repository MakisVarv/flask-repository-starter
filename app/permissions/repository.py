import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.permissions.model import Permission


class PermissionRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(self, name: str) -> Permission | None:

        stmt = select(Permission).where(Permission.name == name)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, name: str) -> bool:

        return self.get_by_name(name) is not None

    def get_all(self):
        statement = select(Permission)
        return self.session.scalars(statement).all()

    def get_by_id(self, permission_id: uuid.UUID):
        return self.session.get(Permission, permission_id)

    def create(self, permission: Permission):
        self.session.add(permission)
        self.session.flush()
        self.session.refresh(permission)
        return permission

    def update(self, permission: Permission, data: dict) -> Permission:
        if "name" in data:
            permission.name = data["name"]

        if "description" in data:
            permission.description = data["description"]

        self.session.flush()
        self.session.refresh(permission)

        return permission

    def delete(self, permission: Permission) -> None:
        self.session.delete(permission)
        self.session.flush()
