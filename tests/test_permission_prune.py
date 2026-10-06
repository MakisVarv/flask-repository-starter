import pytest

from app.config.database import SessionLocal
from app.permissions.model import Permission
from app.permissions.prune_service import PermissionPruneService
from app.permissions.repository import PermissionRepository
from app.roles.repository import RoleRepository


def test_prune_rejects_registered_permission(
    admin_role,
) -> None:
    with SessionLocal() as session:
        service = PermissionPruneService(session)

        with pytest.raises(
            ValueError,
            match="still registered",
        ):
            service.prune("user.read")


def test_prune_rejects_permission_that_does_not_exist(
    admin_role,
) -> None:
    with SessionLocal() as session:
        service = PermissionPruneService(session)

        with pytest.raises(
            ValueError,
            match="does not exist",
        ):
            service.prune("missing.permission")


def test_prune_removes_stale_permission_and_role_assignments(
    admin_role,
    manager_role,
) -> None:
    with SessionLocal() as session:
        permission_repository = PermissionRepository(session)
        role_repository = RoleRepository(session)

        stale_permission = Permission(
            name="legacy.permission",
            description="Old permission",
        )

        session.add(stale_permission)

        admin = role_repository.get_by_name("Admin")
        manager = role_repository.get_by_name("Manager")

        assert admin is not None
        assert manager is not None

        admin.permissions.append(stale_permission)
        manager.permissions.append(stale_permission)

        session.commit()

        service = PermissionPruneService(session)

        service.prune("legacy.permission")

        assert permission_repository.get_by_name("legacy.permission") is None

        admin = role_repository.get_by_name("Admin")
        manager = role_repository.get_by_name("Manager")

        assert admin is not None
        assert manager is not None

        assert "legacy.permission" not in {
            permission.name for permission in admin.permissions
        }

        assert "legacy.permission" not in {
            permission.name for permission in manager.permissions
        }
