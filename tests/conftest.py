import pytest

from app import create_app
from app.config.config import TestingConfig
from app.config.database import SessionLocal
from app.permissions.model import Permission
from app.roles.model import Role
from app.users.service import UserService


@pytest.fixture
def app():
    flask_app = create_app(TestingConfig)

    yield flask_app

    flask_app.extensions["db_engine"].dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def db_transaction(app):
    engine = app.extensions["db_engine"]

    with engine.connect() as connection:
        transaction = connection.begin()

        SessionLocal.configure(
            bind=connection,
            join_transaction_mode="create_savepoint",
        )

        yield

        transaction.rollback()

        SessionLocal.configure(bind=engine)


@pytest.fixture
def user_role(db_transaction):
    with SessionLocal() as session:
        role = Role(
            name="User",
            description="Standard system user",
            level=10,
        )

        session.add(role)
        session.commit()

        return role.id


@pytest.fixture
def regular_user(user_role):
    email = "john@example.com"
    password = "Password123!"

    with SessionLocal() as session:
        user_service = UserService(session)

        user = user_service._create_user(
            first_name="John",
            last_name="Doe",
            email=email,
            password=password,
            role_id=user_role,
        )
        user_id = user.id

    return {
        "id": user_id,
        "email": email,
        "password": password,
    }


@pytest.fixture
def admin_permissions(db_transaction):
    permissions = [
        Permission(name="user.read", description="Read user information"),
        Permission(name="user.create", description="Create users"),
        Permission(name="user.update", description="Update users"),
        Permission(name="user.delete", description="Delete users"),
        Permission(name="user.change_role", description="Change a user's role"),
        Permission(name="role.read", description="Read roles"),
        Permission(name="role.create", description="Create roles"),
        Permission(name="role.update", description="Update roles"),
        Permission(name="role.delete", description="Delete roles"),
        Permission(
            name="role.assign_permission",
            description="Assign or remove permissions from roles",
        ),
        Permission(name="permission.read", description="Read permissions"),
    ]

    with SessionLocal() as session:
        session.add_all(permissions)
        session.commit()

        return [permission.id for permission in permissions]


@pytest.fixture
def admin_role(admin_permissions):
    with SessionLocal() as session:
        permissions: list[Permission] = []

        for permission_id in admin_permissions:
            permission = session.get(Permission, permission_id)

            assert permission is not None

            permissions.append(permission)

        role = Role(
            name="Admin",
            description="System administrator",
            level=100,
        )

        role.permissions.extend(permissions)

        session.add(role)
        session.commit()

        return role.id


@pytest.fixture
def admin_user(admin_role):
    email = "admin@example.com"
    password = "Admin123456!"

    with SessionLocal() as session:
        user_service = UserService(session)

        user_service._create_user(
            first_name="System",
            last_name="Admin",
            email=email,
            password=password,
            role_id=admin_role,
        )

    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def manager_role(admin_permissions):
    with SessionLocal() as session:
        role = Role(
            name="Manager",
            description="Mid-level manager",
            level=50,
        )
        session.add(role)

        for permission_id in admin_permissions:
            permission = session.get(Permission, permission_id)

            assert permission is not None

            role.permissions.append(permission)

        session.commit()

        return role.id


@pytest.fixture
def manager_user(manager_role):
    email = "manager@example.com"
    password = "Manager123!"

    with SessionLocal() as session:
        user_service = UserService(session)

        user = user_service._create_user(
            first_name="Test",
            last_name="Manager",
            email=email,
            password=password,
            role_id=manager_role,
        )

        user_id = user.id

    return {
        "id": user_id,
        "email": email,
        "password": password,
    }
