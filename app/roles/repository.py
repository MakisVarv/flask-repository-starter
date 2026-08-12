import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.roles.model import Role


class RoleRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_name(self, name: str) -> Role | None:

        stmt = select(Role).where(Role.name == name)

        return self.session.execute(stmt).scalar_one_or_none()

    def exists(self, name: str) -> bool:

        return self.get_by_name(name) is not None

    def get_all(self):
        statement = select(Role)
        return self.session.scalars(statement).all()

    def get_by_id(self, role_id: uuid.UUID):
        return self.session.get(Role, role_id)

    def create(self, role: Role):
        self.session.add(role)
        self.session.flush()
        self.session.refresh(role)
        return role

    def update(self, role: Role, data: dict) -> Role:
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
