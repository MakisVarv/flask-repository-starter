import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.roles.model import Role
from app.users.model import User


class UserRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:

        stmt = select(User).where(User.email == email)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, email: str) -> bool:

        return self.get_by_email(email) is not None

    def get_all(self):
        statement = select(User)
        return self.session.scalars(statement).all()

    def get_by_id(self, user_id: uuid.UUID):
        return self.session.get(User, user_id)

    def create(self, user: User):
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return user

    def update(self, user: User, data: dict) -> User:

        allowed_fields = {"first_name", "last_name", "email", "phone"}

        for field, value in data.items():
            if field in allowed_fields:
                setattr(user, field, value)

        self.session.flush()
        self.session.refresh(user)

        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.flush()

    def change_role(self, user: User, role: Role) -> User:
        user.role = role

        self.session.flush()
        self.session.refresh(user)

        return user
