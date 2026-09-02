import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.roles.model import Role
from app.users.model import User


class RoleRepository:

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_name(self, name: str) -> Role | None:

        stmt = select(Role).where(Role.name == name)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, name: str) -> bool:

        return self.get_by_name(name) is not None

    def get_all(self) -> Sequence[Role]:
        statement = select(Role)
        return self.session.scalars(statement).all()

    def get_by_id(self, role_id: uuid.UUID) -> Role | None:
        return self.session.get(Role, role_id)

    def count_users_by_role(self, role_id: uuid.UUID) -> int:
        return (
            self.session.scalar(
                select(func.count(User.id)).where(User.role_id == role_id)
            )
            or 0
        )

    def create(self, role: Role) -> Role:
        self.session.add(role)
        self.session.flush()
        self.session.refresh(role)
        return role

    def update(self, role: Role, data: dict[str, Any]) -> Role:
        if "name" in data:
            role.name = data["name"]

        if "description" in data:
            role.description = data["description"]

        self.session.flush()
        self.session.refresh(role)

        return role

    def delete(self, role: Role) -> None:
        self.session.delete(role)
        self.session.flush()
