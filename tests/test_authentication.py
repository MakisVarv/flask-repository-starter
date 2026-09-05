from sqlalchemy import func, select

from app.auth.model import AuthSession
from app.config.database import SessionLocal
from app.users.model import User
from app.users.repository import UserRepository


def test_users_requires_authentication(client):
    response = client.get("/api/users/")
    data = response.get_json()
    assert response.status_code == 401
    assert "message" in data


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


def test_refresh_token(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    original_access_token = login_response.get_json()["access_token"]

    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert csrf_cookie is not None
    original_refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )

    assert original_refresh_cookie is not None
    refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert refresh_response.status_code == 200

    data = refresh_response.get_json()

    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    assert data["access_token"] != original_access_token

    new_refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )

    assert new_refresh_cookie is not None
    assert new_refresh_cookie.value != original_refresh_cookie.value


def test_old_refresh_token_cannot_be_reused(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    old_refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )
    old_csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert old_refresh_cookie is not None
    assert old_csrf_cookie is not None

    first_refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": old_csrf_cookie.value,
        },
    )

    assert first_refresh_response.status_code == 200

    client.set_cookie(
        "refresh_token_cookie",
        old_refresh_cookie.value,
        path="/api/auth",
    )

    reuse_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": old_csrf_cookie.value,
        },
    )

    assert reuse_response.status_code == 401

    data = reuse_response.get_json()
    assert data["message"] == "Invalid refresh token."


def test_logout(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert csrf_cookie is not None

    logout_response = client.post(
        "/api/auth/logout",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert logout_response.status_code == 200
    assert logout_response.get_json()["message"] == "Logged out successfully."

    refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )

    assert refresh_cookie is None


def test_logout_revokes_auth_session(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    csrf_cookie = client.get_cookie("csrf_refresh_token")
    assert csrf_cookie is not None

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is None

        sid = auth_session.id

    logout_response = client.post(
        "/api/auth/logout",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert logout_response.status_code == 200

    with SessionLocal() as session:
        auth_session = session.get(AuthSession, sid)

        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_revoked_session_cannot_refresh(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )
    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert refresh_cookie is not None
    assert csrf_cookie is not None

    logout_response = client.post(
        "/api/auth/logout",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert logout_response.status_code == 200

    # Restore the old refresh token that logout removed.
    client.set_cookie(
        "refresh_token_cookie",
        refresh_cookie.value,
        path="/api/auth",
    )

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert refresh_response.status_code == 401

    data = refresh_response.get_json()
    assert data["message"] == "Refresh session revoked."


def test_inactive_user_cannot_refresh(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    csrf_cookie = client.get_cookie("csrf_refresh_token")
    assert csrf_cookie is not None

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None

        user.is_active = False
        session.commit()

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert refresh_response.status_code == 401

    data = refresh_response.get_json()
    assert data["message"] == "Invalid refresh session."


def test_refresh_token_reuse_revokes_session(client, regular_user):
    credentials = {
        "email": regular_user["email"],
        "password": regular_user["password"],
    }

    login_response = client.post(
        "/api/auth/login",
        json=credentials,
    )

    assert login_response.status_code == 200

    refresh_a = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )
    csrf_a = client.get_cookie("csrf_refresh_token")

    assert refresh_a is not None
    assert csrf_a is not None

    # A -> B
    first_refresh = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-TOKEN": csrf_a.value},
    )

    assert first_refresh.status_code == 200

    refresh_b = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )
    csrf_b = client.get_cookie("csrf_refresh_token")

    assert refresh_b is not None
    assert csrf_b is not None

    # Replay old token A.
    client.set_cookie(
        "refresh_token_cookie",
        refresh_a.value,
        path="/api/auth",
    )

    replay_response = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-TOKEN": csrf_a.value},
    )

    assert replay_response.status_code == 401

    # Try valid token B after the replay.
    client.set_cookie(
        "refresh_token_cookie",
        refresh_b.value,
        path="/api/auth",
    )

    second_refresh = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-TOKEN": csrf_b.value},
    )

    assert second_refresh.status_code == 401
    assert second_refresh.get_json()["message"] == "Refresh session revoked."
