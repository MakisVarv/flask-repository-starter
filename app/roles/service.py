import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.orm import Session

from app.auth.authorization import MAX_ROLE_LEVEL, PROTECTED_ROLE_NAMES
from app.common.exceptions import ConflictException, ForbiddenException
from app.common.exceptions.not_found import NotFoundException
from app.permissions.model import Permission
from app.permissions.repository import PermissionRepository
from app.roles.model import Role
from app.roles.repository import RoleRepository
from app.users.model import User
from app.users.repository import UserRepository


class RoleService:

    def _ensure_can_manage_role(self, actor: User, role: Role) -> None:
        if actor.role.level == MAX_ROLE_LEVEL:
            return

        if actor.role.level <= role.level:
            raise ForbiddenException("You are not authorized to change this role")

    def _ensure_can_set_role_level(self, actor: User, level: int) -> None:
        if actor.role.level == MAX_ROLE_LEVEL:
            return

        if actor.role.level <= level:
            raise ForbiddenException("You are not authorized to use this role level")

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.repository = RoleRepository(session)
        self.permission_repository = PermissionRepository(session)

    def get_permission(self, permission_id: uuid.UUID) -> Permission:
        permission = self.permission_repository.get_by_id(permission_id)

        if permission is None:
            raise NotFoundException("Permission")

        return permission

    def create_role(
        self,
        actor: User,
        name: str,
        level: int,
        description: str | None = None,
    ) -> Role:

        self._ensure_can_set_role_level(actor, level)

        if self.repository.exists(name):
            raise ConflictException("Role already exists.")

        role = Role(name=name, description=description, level=level)

        try:

            role = self.repository.create(role)
            self.session.commit()
            return role

        except Exception:

            self.session.rollback()
            raise

    def get_roles(self) -> Sequence[Role]:

        return self.repository.get_all()

    def get_role(self, role_id: uuid.UUID) -> Role:

        role = self.repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        return role

    def update_role(
        self, actor: User, role_id: uuid.UUID, data: dict[str, Any]
    ) -> Role:
        role = self.get_role(role_id)
        self._ensure_can_manage_role(actor, role)
        if role.name in PROTECTED_ROLE_NAMES:
            if "name" in data or "level" in data:
                raise ConflictException(
                    "Built-in role name and level cannot be changed."
                )
        if "level" in data:
            self._ensure_can_set_role_level(actor, data["level"])
        if "name" in data:
            existing = self.repository.get_by_name(data["name"])
            if existing and existing.id != role.id:
                raise ConflictException("Role already exists.")
        try:
            role = self.repository.update(role, data)
            self.session.commit()
            return role
        except Exception:
            self.session.rollback()
            raise

    def delete_role(self, actor: User, role_id: uuid.UUID) -> None:
        role = self.get_role(role_id)
        self._ensure_can_manage_role(actor, role)

        if role.name in PROTECTED_ROLE_NAMES:
            raise ConflictException("Built-in roles cannot be deleted.")

        user_count = self.user_repository.count_by_role(role_id)

        if user_count > 0:
            raise ConflictException(
                "Role cannot be deleted while users are assigned to it."
            )
        try:
            self.repository.delete(role)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def assign_permission(
        self,
        actor: User,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Role:
        role = self.get_role(role_id)
        self._ensure_can_manage_role(actor, role)
        permission = self.get_permission(permission_id)

        if permission in role.permissions:
            raise ConflictException("Permission already assigned to role.")

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
        actor: User,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Role:
        role = self.get_role(role_id)
        self._ensure_can_manage_role(actor, role)
        permission = self.get_permission(permission_id)

        if permission not in role.permissions:
            raise ConflictException("Permission not assigned to role.")

        try:
            role.permissions.remove(permission)
            self.session.commit()
            self.session.refresh(role)
            return role
        except Exception:
            self.session.rollback()
            raise
