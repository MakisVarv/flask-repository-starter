from sqlalchemy.orm import Session

from app.config.permissions import PERMISSIONS
from app.permissions.repository import PermissionRepository


class PermissionPruneService:
    def __init__(self, session: Session) -> None:
        self.permission_repository = PermissionRepository(session)
        self.session = session

    def prune(self, permission_name: str) -> None:
        configured_names = {permission["name"] for permission in PERMISSIONS}

        if permission_name in configured_names:
            raise ValueError(
                f"Permission '{permission_name}' is still registered and cannot be pruned."
            )

        permission = self.permission_repository.get_by_name(permission_name)

        if permission is None:
            raise ValueError(f"Permission '{permission_name}' does not exist.")

        try:
            for role in list(permission.roles):
                role.permissions.remove(permission)

            self.permission_repository.delete(permission)

            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
