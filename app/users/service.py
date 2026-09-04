import uuid
from collections.abc import Sequence

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.auth.authorization import MAX_ROLE_LEVEL, ForbiddenException
from app.common.exceptions.bad_request import BadRequestException
from app.common.exceptions.conflict import ConflictException
from app.common.exceptions.not_found import NotFoundException
from app.roles.model import Role
from app.roles.repository import RoleRepository
from app.users.model import User
from app.users.repository import UserRepository


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)

    def _ensure_can_manage_user(self, actor: User, target: User) -> None:
        if actor.role.level == MAX_ROLE_LEVEL:
            return
        if actor.role.level <= target.role.level:
            raise ForbiddenException("You are not authorized to change this user")

    def _ensure_can_assign_role(self, actor: User, role: Role) -> None:
        if actor.role.level == MAX_ROLE_LEVEL:
            return

        if actor.role.level <= role.level:
            raise ForbiddenException("You are not authorized to assign this role")

    def get_role(self, role_id: uuid.UUID) -> Role:
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        return role

    def _create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_id: uuid.UUID,
        phone: str | None = None,
    ) -> User:
        if self.repository.get_by_email(email):
            raise BadRequestException("Email already exists.")

        password_hash = generate_password_hash(password)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            role_id=role_id,
        )
        try:

            user = self.repository.create(user)
            self.session.commit()
            return user

        except Exception:

            self.session.rollback()
            raise

    def create_user(
        self,
        actor: User,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role_id: uuid.UUID,
        phone: str | None = None,
    ) -> User:

        role = self.get_role(role_id)
        self._ensure_can_assign_role(actor, role)

        return self._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role_id=role_id,
            phone=phone,
        )

    def get_users(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        sort: str = "id",
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[Sequence[User], dict[str, int]]:
        descending = sort.startswith("-")
        sort_field = sort.removeprefix("-")
        users = self.repository.get_all(
            page=page,
            page_size=page_size,
            search=search,
            role=role,
            is_active=is_active,
            sort_field=sort_field,
            descending=descending,
        )

        total = self.repository.count(
            search=search,
            role=role,
            is_active=is_active,
        )

        total_pages = (total + page_size - 1) // page_size

        return users, {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }

    def get_user(self, user_id: uuid.UUID) -> User:

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException("User")

        return user

    def update_user(self, actor: User, user_id: uuid.UUID, data: dict) -> User:

        user = self.get_user(user_id)

        self._ensure_can_manage_user(actor, user)
        if "email" in data:
            existing = self.repository.get_by_email(data["email"])

            if existing and existing.id != user.id:
                raise BadRequestException("Email already exists.")

        try:
            user = self.repository.update(user, data)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise

    def delete_user(self, actor: User, user_id: uuid.UUID) -> None:
        user = self.get_user(user_id)
        self._ensure_can_manage_user(actor, user)
        if user.is_active:
            raise ConflictException(
                "Active users must be deactivated before they can be deleted."
            )
        try:
            self.repository.delete(user)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def change_role(self, actor: User, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        user = self.get_user(user_id)

        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        self._ensure_can_manage_user(actor, user)
        self._ensure_can_assign_role(actor, role)
        try:
            user = self.repository.change_role(user, role)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise

    def change_status(self, actor: User, user_id: uuid.UUID, is_active: bool) -> User:
        user = self.get_user(user_id)

        self._ensure_can_manage_user(actor, user)

        try:
            user = self.repository.update_status(user, is_active)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise
