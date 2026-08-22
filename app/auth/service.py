import uuid
from typing import Any

from flask_jwt_extended import create_access_token
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

from app.common.exceptions import NotFoundException, UnauthorizedException
from app.roles import RoleRepository
from app.users import UserRepository, UserService
from app.users.model import User


class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.role_repository = RoleRepository(session)
        self.user_service = UserService(session)
        self.user_repository = UserRepository(session)

    def register(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        phone: str | None = None,
    ) -> User:
        user_role = self.role_repository.get_by_name("User")

        if user_role is None:
            raise NotFoundException("User role")

        return self.user_service.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            phone=phone,
            role_id=user_role.id,
        )

    def login(
        self,
        email: str,
        password: str,
    ) -> tuple[User, str]:

        user = self.user_repository.get_by_email(email)

        if user is None:
            raise UnauthorizedException("Invalid email or password.")

        password_ok = check_password_hash(user.password_hash, password)

        if not user.is_active:
            raise UnauthorizedException("Invalid email or password.")
        if not password_ok:
            raise UnauthorizedException("Invalid email or password.")

        access_token = create_access_token(identity=str(user.id))

        return user, access_token

    def get_current_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException("User")

        if not user.is_active:
            raise UnauthorizedException("Account is inactive.")

        return user

    def update_current_user(self, user_id: uuid.UUID, data: dict[str, Any]) -> User:
        user = self.get_current_user(user_id)
        if "first_name" in data:
            user.first_name = data["first_name"]

        if "last_name" in data:
            user.last_name = data["last_name"]

        if "phone" in data:
            user.phone = data["phone"]

        self.session.commit()

        return user
