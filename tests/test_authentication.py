from sqlalchemy import func, select

from app.config.database import SessionLocal
from app.users import User, UserRepository


def test_users_requires_authentication(client):
    response = client.get("/api/users/")

    assert response.status_code == 401


def test_register_user(client, user_role):
    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["email"] == "john@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_email("john@example.com")

        assert user is not None
        assert user.email == "john@example.com"


def test_register_duplicate_email(client, user_role):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Password123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    data = second_response.get_json()
    assert data["message"] == "Email already exists."
    with SessionLocal() as session:
        user_repository = UserRepository(session)
        count = user_repository.session.scalar(
            select(func.count(User.id)).where(User.email == "john@example.com")
        )
        assert count == 1


def test_login_user(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }
    response = client.post(
        "/api/auth/login",
        json=credentials,
    )
    data = response.get_json()
    assert response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


def test_invalid_login(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }
    invalid_credentials = {
        **credentials,
        "password": "Password",
    }
    response = client.post(
        "/api/auth/login",
        json=invalid_credentials,
    )
    data = response.get_json()
    assert response.status_code == 401
    assert "access_token" not in data
    assert data["message"] == "Invalid email or password."


def test_login_with_unknown_email(client):
    invalid_credentials = {"email": "notjohn@example.com", "password": "Password"}
    response = client.post(
        "/api/auth/login",
        json=invalid_credentials,
    )
    data = response.get_json()
    assert response.status_code == 401
    assert "access_token" not in data
    assert data["message"] == "Invalid email or password."


def test_regular_user_without_permission_is_forbidden(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }
    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )
    data = login_response.get_json()
    assert login_response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    access_token = data["access_token"]
    second_response = client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert second_response.status_code == 403
    data = second_response.get_json()
    assert data["message"] == "You do not have permission to perform this action."


def test_admin_can_read_users(client, admin_user):
    login_response = client.post(
        "/api/auth/login",
        json=admin_user,
    )
    data = login_response.get_json()
    assert login_response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    access_token = data["access_token"]
    second_response = client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert second_response.status_code == 200


def test_invalid_token(client):
    access_token = "not_a_real_token"
    second_response = client.get(
        "/api/users/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert second_response.status_code == 401


def test_register_invalid_email(client):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "not-an-email",
        "password": "Password123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload,
    )
    data = first_response.get_json()
    assert first_response.status_code == 400
    assert "errors" in data
    assert "email" in data["errors"]
    assert "Not a valid email address." in data["errors"]["email"]


def test_register_invalid_password(client):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Pass123",
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload,
    )
    data = first_response.get_json()
    assert first_response.status_code == 400
    assert "errors" in data
    assert "password" in data["errors"]
    assert "Shorter than minimum length 8." in data["errors"]["password"]


def test_register_missing_email(client):
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "password": "Password123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=payload,
    )
    data = first_response.get_json()
    assert first_response.status_code == 400
    assert "errors" in data
    assert "email" in data["errors"]
    assert "Missing data for required field." in data["errors"]["email"]


def test_register_missing_password(client):
    payload = {"first_name": "John", "last_name": "Doe", "email": "john@example.com"}

    first_response = client.post(
        "/api/auth/register",
        json=payload,
    )
    data = first_response.get_json()
    assert first_response.status_code == 400
    assert "errors" in data
    assert "password" in data["errors"]
    assert "Missing data for required field." in data["errors"]["password"]


def test_me(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }
    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )
    data = login_response.get_json()
    assert login_response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    access_token = data["access_token"]
    me_response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    me_data = me_response.get_json()
    assert me_response.status_code == 200
    assert "email" in me_data
    assert me_data["email"] == credentials["email"]
    assert me_data["id"] == str(regular_user["id"])


def test_update_me(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    access_token = login_response.get_json()["access_token"]

    payload = {
        "first_name": "Johnny",
        "last_name": "Updated",
        "phone": "123456789",
    }

    response = client.patch(
        "/api/auth/me",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["first_name"] == "Johnny"
    assert data["last_name"] == "Updated"
    assert data["phone"] == "123456789"

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None
        assert user.first_name == "Johnny"
        assert user.last_name == "Updated"
        assert user.phone == "123456789"


def test_invalid_update_me(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    access_token = login_response.get_json()["access_token"]

    payload = {}

    response = client.patch(
        "/api/auth/me",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400

    data = response.get_json()

    assert "errors" in data
    assert "_schema" in data["errors"]
    assert "At least one field must be provided." in data["errors"]["_schema"]


def test_inactive_user_cannot_use_existing_token(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None

        user.is_active = False
        session.commit()

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 401
    assert data["message"] == "Account is inactive."
