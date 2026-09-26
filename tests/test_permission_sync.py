import pytest

from app.config.database import SessionLocal
from app.permissions.model import Permission
from app.permissions.repository import PermissionRepository
from app.permissions.sync_service import PermissionSyncService
from app.roles.repository import RoleRepository


def test_sync_creates_missing_permission_and_assigns_it_to_admin(
    admin_role,
) -> None:
    with SessionLocal() as session:
        permission_repository = PermissionRepository(session)
        role_repository = RoleRepository(session)

        existing_permission = permission_repository.get_by_name("dashboard.read")

        assert existing_permission is None

        admin = role_repository.get_by_name("Admin")

        assert admin is not None
        assert "dashboard.read" not in {
            permission.name for permission in admin.permissions
        }

        service = PermissionSyncService(session)

        result = service.sync()

        created_permission = permission_repository.get_by_name("dashboard.read")

        assert created_permission is not None
        assert created_permission.description == "View dashboard"

        assert "dashboard.read" in result.created

        admin = role_repository.get_by_name("Admin")

        assert admin is not None

        admin_permission_names = {permission.name for permission in admin.permissions}

        assert "dashboard.read" in admin_permission_names


def test_sync_updates_changed_permission_description(
    admin_role,
) -> None:
    with SessionLocal() as session:
        permission_repository = PermissionRepository(session)

        permission = permission_repository.get_by_name("user.read")

        assert permission is not None

        permission.description = "Old description"
        session.commit()

        service = PermissionSyncService(session)

        result = service.sync()

        updated_permission = permission_repository.get_by_name("user.read")

        assert updated_permission is not None
        assert updated_permission.description == "Read user information"

        assert "user.read" in result.updated


def test_sync_is_idempotent(
    admin_role,
) -> None:
    with SessionLocal() as session:
        service = PermissionSyncService(session)

        first_result = service.sync()
        second_result = service.sync()

        assert "dashboard.read" in first_result.created

        assert second_result.created == []
        assert second_result.updated == []

        assert "dashboard.read" in second_result.unchanged


def test_sync_reports_stale_permission_without_deleting_it(
    admin_role,
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

        assert admin is not None

        admin.permissions.append(stale_permission)

        session.commit()

        service = PermissionSyncService(session)

        result = service.sync()

        assert "legacy.permission" in result.stale

        persisted = permission_repository.get_by_name("legacy.permission")

        assert persisted is not None
        assert persisted.description == "Old permission"

        admin = role_repository.get_by_name("Admin")

        assert admin is not None

        admin_permission_names = {permission.name for permission in admin.permissions}

        assert "legacy.permission" in admin_permission_names


def test_sync_reports_unchanged_permissions(
    admin_role,
) -> None:
    with SessionLocal() as session:
        service = PermissionSyncService(session)

        service.sync()

        result = service.sync()

        assert "user.read" in result.unchanged
        assert "user.create" in result.unchanged
        assert "dashboard.read" in result.unchanged

        assert result.created == []
        assert result.updated == []


def test_sync_rolls_back_when_admin_role_is_missing(
    db_transaction,
) -> None:
    with SessionLocal() as session:
        permission_repository = PermissionRepository(session)

        assert permission_repository.get_by_name("dashboard.read") is None

        service = PermissionSyncService(session)

        with pytest.raises(
            RuntimeError,
            match="Admin role does not exist",
        ):
            service.sync()

        # Permissions created before the Admin failure must
        # have been rolled back with the whole synchronization.
        assert permission_repository.get_by_name("dashboard.read") is None

        assert permission_repository.get_by_name("user.read") is None
