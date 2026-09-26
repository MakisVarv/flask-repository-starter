from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config.permissions import PERMISSIONS
from app.permissions.model import Permission
from app.permissions.repository import PermissionRepository
from app.roles.repository import RoleRepository


@dataclass
class PermissionSyncResult:
    created: list[str]
    updated: list[str]
    unchanged: list[str]
    stale: list[str]


class PermissionSyncService:

    def __init__(self, session: Session) -> None:
        self.permission_repository = PermissionRepository(session)
        self.role_repository = RoleRepository(session)
        self.session = session

    def sync(self) -> PermissionSyncResult:
        try:
            config_by_name = self._build_config_lookup()
            db_by_name = self._build_database_lookup()
            missing = self._find_missing(
                config_by_name=config_by_name, db_by_name=db_by_name
            )
            changed = self._find_changed(
                config_by_name=config_by_name, db_by_name=db_by_name
            )
            unchanged = self._find_unchanged(
                config_by_name=config_by_name, db_by_name=db_by_name
            )

            created_permissions = self._create_missing(
                missing=missing,
                config_by_name=config_by_name,
            )

            for permission in created_permissions:
                db_by_name[permission.name] = permission

            self._update_changed(
                changed=changed,
                config_by_name=config_by_name,
                db_by_name=db_by_name,
            )
            self._sync_admin_permissions(
                config_by_name=config_by_name,
                db_by_name=db_by_name,
            )
            stale = self._find_stale(
                config_by_name=config_by_name, db_by_name=db_by_name
            )
            result = PermissionSyncResult(
                created=missing,
                updated=changed,
                unchanged=unchanged,
                stale=stale,
            )
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise

    def _build_config_lookup(self) -> dict[str, dict[str, str]]:

        config_by_name = {permission["name"]: permission for permission in PERMISSIONS}

        return config_by_name

    def _build_database_lookup(self) -> dict[str, Permission]:
        permissions = self.permission_repository.get_all()
        db_by_name = {permission.name: permission for permission in permissions}
        return db_by_name

    def _find_missing(
        self,
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> list[str]:
        missing = [name for name in config_by_name if name not in db_by_name]
        return missing

    def _find_stale(
        self,
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> list[str]:
        stale = [name for name in db_by_name if name not in config_by_name]
        return stale

    def _find_changed(
        self,
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> list[str]:
        changed = [
            name
            for name in config_by_name
            if name in db_by_name
            and config_by_name[name]["description"] != db_by_name[name].description
        ]
        return changed

    def _find_unchanged(
        self,
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> list[str]:
        unchanged = [
            name
            for name in config_by_name
            if name in db_by_name
            and config_by_name[name]["description"] == db_by_name[name].description
        ]
        return unchanged

    def _create_missing(
        self,
        missing: list[str],
        config_by_name: dict[str, dict[str, str]],
    ) -> list[Permission]:
        created_permissions = []

        for name in missing:
            definition = config_by_name[name]
            new_permission = Permission(
                name=definition["name"],
                description=definition["description"],
            )
            created = self.permission_repository.create(new_permission)
            created_permissions.append(created)
        return created_permissions

    def _update_changed(
        self,
        changed: list[str],
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> None:
        for name in changed:
            definition = config_by_name[name]
            permission = db_by_name[name]

            self.permission_repository.update(
                permission,
                {
                    "description": definition["description"],
                },
            )

    def _sync_admin_permissions(
        self,
        config_by_name: dict[str, dict[str, str]],
        db_by_name: dict[str, Permission],
    ) -> None:
        admin_role = self.role_repository.get_by_name("Admin")
        if admin_role is None:
            raise RuntimeError("Admin role does not exist!")
        admin_permission_names = {
            permission.name for permission in admin_role.permissions
        }
        for configured_name in config_by_name:
            if configured_name not in admin_permission_names:
                admin_role.permissions.append(db_by_name[configured_name])
