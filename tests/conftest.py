import pytest

from app import create_app
from app.config.config import TestingConfig
from app.config.database import SessionLocal
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
