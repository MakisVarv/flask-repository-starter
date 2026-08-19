import pytest

from app import create_app
from app.common.exceptions.not_found import NotFoundException
from app.config.config import TestingConfig
from app.config.database import SessionLocal
from app.permissions import Permission
from app.roles.model import Role
from app.users import UserService


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    print("\nTEST DATABASE:", app.config["DATABASE_URL"])

    yield app

    app.extensions["db_engine"].dispose()


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

        user_service.create_user(
            first_name="John",
            last_name="Doe",
            email=email,
            password=password,
            role_id=user_role,
        )

    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def user_read_permission(db_transaction):
    with SessionLocal() as session:
        permission = Permission(
            name="user.read",
            description="Read user information",
        )

        session.add(permission)
        session.commit()

        return permission.id


@pytest.fixture
def admin_role(user_read_permission):
    with SessionLocal() as session:
        permission = session.get(Permission, user_read_permission)

        assert permission is not None

        role = Role(
            name="Admin",
            description="System administrator",
        )

        role.permissions.append(permission)

        session.add(role)
        session.commit()

        return role.id


@pytest.fixture
def admin_user(admin_role):
    email = "admin@example.com"
    password = "Admin123456!"

    with SessionLocal() as session:
        user_service = UserService(session)

        user_service.create_user(
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
