import uuid

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app.common.exceptions.bad_request import BadRequestException
from app.common.exceptions.not_found import NotFoundException
from app.roles.repository import RoleRepository
from app.users.model import User
from app.users.repository import UserRepository


class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.repository = UserRepository(session)
        self.role_repository = RoleRepository(session)

    def get_role(self, role_id: uuid.UUID):
        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        return role

    def create_user(
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

        self.get_role(role_id)

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

    def get_users(self):

        return self.repository.get_all()

    def get_user(self, user_id):

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundException("User")

        return user

    def update_user(self, user_id, data: dict):
        """Update an existing user."""

        user = self.get_user(user_id)

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

    def delete_user(self, user_id: uuid.UUID) -> None:
        user = self.get_user(user_id)

        try:
            self.repository.delete(user)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def change_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        user = self.get_user(user_id)

        role = self.role_repository.get_by_id(role_id)

        if role is None:
            raise NotFoundException("Role")

        try:
            user = self.repository.change_role(user, role)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise
