import uuid

from sqlalchemy.orm import Session

from app.common.exceptions.base_exception import AppException
from app.common.exceptions.not_found import NotFoundException
from app.permissions.repository import PermissionRepository
from app.roles.model import Role
from app.roles.repository import RoleRepository


class RoleService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = RoleRepository(session)
        self.permission_repository = PermissionRepository(session)

    def get_permission(self, permission_id: uuid.UUID):
        permission = self.permission_repository.get_by_id(permission_id)

        if permission is None:
            raise NotFoundException("Permission")

        return permission

    def create_role(
        self,
        name: str,
        description: str | None = None,
    ) -> Role:

        if self.repository.exists(name):
            raise AppException("Role already exists.", 409)

        role = Role(
            name=name,
            description=description,
        )

        try:

            role = self.repository.create(role)
            self.session.commit()
            return role

        except Exception:

            self.session.rollback()
            raise

    def get_roles(self):

        return self.repository.get_all()

    def get_role(self, role_id):

        role = self.repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        return role

    def update_role(self, role_id: uuid.UUID, data: dict) -> Role:
        role = self.get_role(role_id)
        if "name" in data:
            existing = self.repository.get_by_name(data["name"])
            if existing and existing.id != role.id:
                raise AppException("Role already exists.", 409)
        try:
            role = self.repository.update(role, data)
            self.session.commit()
            return role
        except Exception:
            self.session.rollback()
            raise

    def delete_role(self, role_id: uuid.UUID) -> None:
        role = self.get_role(role_id)

        try:
            self.repository.delete(role)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def assign_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Role:
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)

        if permission in role.permissions:
            raise AppException("Permission already assigned to role.", 409)

        try:
            role.permissions.append(permission)
            self.session.commit()
            self.session.refresh(role)
            return role
        except Exception:
            self.session.rollback()
            raise

    def remove_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Role:
        role = self.get_role(role_id)
        permission = self.get_permission(permission_id)

        if permission not in role.permissions:
            raise AppException("Permission not assigned to role.", 409)

        try:
            role.permissions.remove(permission)
            self.session.commit()
            self.session.refresh(role)
            return role
        except Exception:
            self.session.rollback()
            raise
