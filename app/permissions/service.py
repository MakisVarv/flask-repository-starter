import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.common.exceptions import ConflictException
from app.common.exceptions.base_exception import AppException
from app.common.exceptions.not_found import NotFoundException
from app.permissions.model import Permission
from app.permissions.repository import PermissionRepository


class PermissionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PermissionRepository(session)

    def create_permission(
        self,
        name: str,
        description: str | None = None,
    ) -> Permission:

        if self.repository.exists(name):
            raise ConflictException("Permission already exists.")

        permission = Permission(
            name=name,
            description=description,
        )
        try:
            permission = self.repository.create(permission)
            self.session.commit()
            return permission
        except Exception:
            self.session.rollback()
            raise

    def get_permissions(self) -> Sequence[Permission]:

        return self.repository.get_all()

    def get_permission(self, permission_id: uuid.UUID) -> Permission:

        permission = self.repository.get_by_id(permission_id)

        if permission is None:
            raise NotFoundException("Permission")

        return permission

    def update_permission(
        self, permission_id: uuid.UUID, data: dict[str, Any]
    ) -> Permission:
        permission = self.get_permission(permission_id)
        if "name" in data:
            existing = self.repository.get_by_name(data["name"])
            if existing and existing.id != permission.id:
                raise ConflictException("Permission already exists.")
        try:
            permission = self.repository.update(permission, data)
            self.session.commit()
            return permission
        except Exception:
            self.session.rollback()
            raise

    def delete_permission(self, permission_id: uuid.UUID) -> None:
        permission = self.get_permission(permission_id)

        try:
            self.repository.delete(permission)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
