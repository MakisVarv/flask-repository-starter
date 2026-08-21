import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.roles.model import Role
from app.users.model import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def _apply_filters(
        self,
        statement,
        search=None,
        role: str | None = None,
        is_active: bool | None = None,
    ):
        if search:
            pattern = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        if role:
            statement = statement.where(User.role.has(Role.name.ilike(role.strip())))
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        return statement

    def get_by_email(self, email: str) -> User | None:

        stmt = select(User).where(User.email == email)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, email: str) -> bool:

        return self.get_by_email(email) is not None

    def get_all(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ):

        offset = (page - 1) * page_size
        statement = select(User)
        statement = self._apply_filters(statement, search, role, is_active)

        statement = statement.order_by(User.id).offset(offset).limit(page_size)
        return self.session.scalars(statement).all()

    def get_by_id(self, user_id: uuid.UUID):
        return self.session.get(User, user_id)

    def count(
        self,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ):
        statement = select(func.count(User.id))
        statement = self._apply_filters(statement, search, role, is_active)
        return self.session.scalar(statement) or 0

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
