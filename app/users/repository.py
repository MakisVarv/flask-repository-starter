import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.common.pagination import Pagination
from app.common.query_options import QueryOptions
from app.common.sorting import apply_sorting
from app.roles.model import Role
from app.users.model import User


class UserRepository(BaseRepository[User]):

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def _apply_filters(
        self,
        statement,
        search: str | None = None,
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

    def get_page(
        self,
        options: QueryOptions,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[Sequence[User], dict[str, int | bool]]:

        statement = select(User)
        statement = self._apply_filters(
            statement,
            search=search,
            role=role,
            is_active=is_active,
        )
        count_statement = select(func.count(User.id))
        count_statement = self._apply_filters(
            count_statement,
            search=search,
            role=role,
            is_active=is_active,
        )

        sort_columns = {
            "id": User.id,
            "first_name": User.first_name,
            "last_name": User.last_name,
            "email": User.email,
            "is_active": User.is_active,
        }
        if options.sort_field == "role":
            statement = statement.join(User.role)

            order = Role.name.desc() if options.descending else Role.name.asc()

            statement = statement.order_by(order, User.id.asc())

        else:
            statement = apply_sorting(
                statement=statement,
                sort_columns=sort_columns,
                sort_field=options.sort_field,
                descending=options.descending,
                secondary_column=User.id,
            )

        return Pagination.paginate(
            session=self.session,
            statement=statement,
            count_statement=count_statement,
            page=options.page,
            page_size=options.page_size,
        )

    def count_by_role(self, role_id: uuid.UUID) -> int:
        return (
            self.session.scalar(
                select(func.count(User.id)).where(User.role_id == role_id)
            )
            or 0
        )

    def update(self, user: User, data: dict[str, Any]) -> User:

        allowed_fields = {"first_name", "last_name", "email", "phone"}

        for field, value in data.items():
            if field in allowed_fields:
                setattr(user, field, value)

        self.session.flush()
        self.session.refresh(user)

        return user

    def update_status(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        self.session.flush()
        return user

    def change_role(self, user: User, role: Role) -> User:
        user.role = role

        self.session.flush()
        self.session.refresh(user)

        return user
