from sqlalchemy import select

from app.config.database import SessionLocal
from app.permissions.model import Permission
from app.roles.model import Role
from app.roles.repository import RoleRepository
from app.roles.service import RoleService
from app.users.repository import UserRepository
from app.users.service import UserService


def get_access_token(client, credentials):
    response = client.post(
        "/api/auth/login",
        json={
            "email": credentials["email"],
            "password": credentials["password"],
        },
    )

    assert response.status_code == 200

    return response.get_json()["access_token"]


def create_test_role(name, level, description="Test role"):
    with SessionLocal() as session:
        role = Role(
            name=name,
            description=description,
            level=level,
        )

        session.add(role)
        session.commit()

        return role.id


def test_update_role_persists_level(admin_user):
    with SessionLocal() as session:
        user_repository = UserRepository(session)
        actor = user_repository.get_by_email(admin_user["email"])

        assert actor is not None

        role = Role(
            name="Manager",
            description="Manager role",
            level=40,
        )

        session.add(role)
        session.commit()

        role_id = role.id

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        actor = user_repository.get_by_email(admin_user["email"])

        assert actor is not None

        service = RoleService(session)

        service.update_role(
            actor=actor,
            role_id=role_id,
            data={"level": 30},
        )

        session.commit()

    with SessionLocal() as session:
        role_repository = RoleRepository(session)
        persisted_role = role_repository.get_by_id(role_id)

        assert persisted_role is not None
        assert persisted_role.level == 30


def test_can_create_role_below_actor_level(client, manager_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": manager_user["email"],
            "password": manager_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/roles/",
        json={
            "name": "Supervisor",
            "description": "Supervisor role",
            "level": 40,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["name"] == "Supervisor"
    assert data["level"] == 40

    with SessionLocal() as session:
        role_repository = RoleRepository(session)
        persisted_role = role_repository.get_by_name("Supervisor")

        assert persisted_role is not None
        assert persisted_role.level == 40


def test_cannot_create_equal_level_role(client, manager_user):
    access_token = get_access_token(client, manager_user)

    response = client.post(
        "/api/roles/",
        json={
            "name": "Equal Manager",
            "description": "Should not be created",
            "level": 50,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        repository = RoleRepository(session)

        assert repository.get_by_name("Equal Manager") is None


def test_cannot_create_higher_level_role(client, manager_user):
    access_token = get_access_token(client, manager_user)

    response = client.post(
        "/api/roles/",
        json={
            "name": "Senior Manager",
            "description": "Should not be created",
            "level": 60,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        repository = RoleRepository(session)

        assert repository.get_by_name("Senior Manager") is None


def test_can_update_lower_level_role(client, manager_user):
    role_id = create_test_role(
        name="Supervisor",
        level=40,
        description="Original description",
    )

    access_token = get_access_token(client, manager_user)

    response = client.patch(
        f"/api/roles/{role_id}",
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        repository = RoleRepository(session)
        role = repository.get_by_id(role_id)

        assert role is not None
        assert role.description == "Updated description"


def test_cannot_update_equal_level_role(client, manager_user):
    role_id = create_test_role(
        name="Peer Manager",
        level=50,
        description="Original description",
    )

    access_token = get_access_token(client, manager_user)

    response = client.patch(
        f"/api/roles/{role_id}",
        json={"description": "Forbidden update"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        repository = RoleRepository(session)
        role = repository.get_by_id(role_id)

        assert role is not None
        assert role.description == "Original description"


def test_cannot_update_higher_level_role(client, manager_user):
    role_id = create_test_role(
        name="Director",
        level=60,
        description="Original description",
    )

    access_token = get_access_token(client, manager_user)

    response = client.patch(
        f"/api/roles/{role_id}",
        json={"description": "Forbidden update"},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        repository = RoleRepository(session)
        role = repository.get_by_id(role_id)

        assert role is not None
        assert role.description == "Original description"


def test_cannot_delete_assigned_role(client, admin_user):
    role_id = create_test_role(
        name="Assigned Role",
        level=40,
    )

    with SessionLocal() as session:
        user_service = UserService(session)

        user_service._create_user(
            first_name="Assigned",
            last_name="User",
            email="assigned@example.com",
            password="Password123!",
            role_id=role_id,
        )

    access_token = get_access_token(client, admin_user)

    response = client.delete(
        f"/api/roles/{role_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 409

    with SessionLocal() as session:
        repository = RoleRepository(session)

        assert repository.get_by_id(role_id) is not None


def get_permission_id(name):
    with SessionLocal() as session:
        permission = session.scalar(select(Permission).where(Permission.name == name))

        assert permission is not None

        return permission.id


def test_can_assign_permission_to_lower_level_role(client, manager_user):
    role_id = create_test_role("Permission Target", 40)
    permission_id = get_permission_id("permission.read")

    access_token = get_access_token(client, manager_user)

    response = client.post(
        f"/api/roles/{role_id}/permissions",
        json={"permission_id": str(permission_id)},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code in (200, 204)

    with SessionLocal() as session:
        role = session.get(Role, role_id)

        assert role is not None
        assert any(permission.id == permission_id for permission in role.permissions)


def test_cannot_assign_permission_to_equal_level_role(client, manager_user):
    role_id = create_test_role("Equal Permission Target", 50)
    permission_id = get_permission_id("permission.read")

    access_token = get_access_token(client, manager_user)

    response = client.post(
        f"/api/roles/{role_id}/permissions",
        json={"permission_id": str(permission_id)},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        role = session.get(Role, role_id)

        assert role is not None
        assert all(permission.id != permission_id for permission in role.permissions)


def create_role_with_permission(name, level, permission_id):
    with SessionLocal() as session:
        permission = session.get(Permission, permission_id)

        assert permission is not None

        role = Role(
            name=name,
            description="Permission test role",
            level=level,
        )

        role.permissions.append(permission)

        session.add(role)
        session.commit()

        return role.id


def test_can_remove_permission_from_lower_level_role(client, manager_user):
    permission_id = get_permission_id("permission.read")

    role_id = create_role_with_permission(
        "Removal Target",
        40,
        permission_id,
    )

    access_token = get_access_token(client, manager_user)

    response = client.delete(
        f"/api/roles/{role_id}/permissions/{permission_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code in (200, 204)

    with SessionLocal() as session:
        role = session.get(Role, role_id)

        assert role is not None
        assert all(permission.id != permission_id for permission in role.permissions)


def test_cannot_remove_permission_from_equal_level_role(
    client,
    manager_user,
):
    permission_id = get_permission_id("permission.read")

    role_id = create_role_with_permission(
        "Equal Removal Target",
        50,
        permission_id,
    )

    access_token = get_access_token(client, manager_user)

    response = client.delete(
        f"/api/roles/{role_id}/permissions/{permission_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403

    with SessionLocal() as session:
        role = session.get(Role, role_id)

        assert role is not None
        assert any(permission.id == permission_id for permission in role.permissions)


def test_cannot_delete_builtin_user_role(client, admin_user, user_role):
    access_token = get_access_token(client, admin_user)

    response = client.delete(
        f"/api/roles/{user_role}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 409
    assert data["message"] == "Built-in roles cannot be deleted."

    with SessionLocal() as session:
        repository = RoleRepository(session)
        role = repository.get_by_id(user_role)

        assert role is not None
        assert role.name == "User"


def test_cannot_delete_builtin_admin_role(client, admin_user, admin_role):
    access_token = get_access_token(client, admin_user)

    response = client.delete(
        f"/api/roles/{admin_role}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 409
    assert data["message"] == "Built-in roles cannot be deleted."

    with SessionLocal() as session:
        repository = RoleRepository(session)
        role = repository.get_by_id(admin_role)

        assert role is not None
        assert role.name == "Admin"
