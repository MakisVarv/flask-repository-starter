from flask_jwt_extended import decode_token
from sqlalchemy import func, select
from werkzeug.security import check_password_hash

from app.auth.model import AuthSession
from app.config.database import SessionLocal
from app.users.model import User
from app.users.repository import UserRepository


def test_reauthenticate_returns_fresh_access_token(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/reauthenticate",
        json={
            "current_password": regular_user["password"],
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    fresh_access_token = response.get_json()["access_token"]

    with client.application.app_context():
        original_payload = decode_token(access_token)
        fresh_payload = decode_token(fresh_access_token)

    assert fresh_payload["sub"] == str(regular_user["id"])
    assert fresh_payload["fresh"] is not False
    assert fresh_payload["sid"] == original_payload["sid"]


def test_logout_all(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert (
        response.get_json()["message"] == "Logged out from all sessions successfully."
    )

    refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )

    assert refresh_cookie is None


def test_logout_all_revokes_every_user_session(client, regular_user):
    # First session
    first_login = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert first_login.status_code == 200

    # Second session
    second_login = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert second_login.status_code == 200

    access_token = second_login.get_json()["access_token"]

    with SessionLocal() as session:
        auth_sessions = session.scalars(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        ).all()

        assert len(auth_sessions) == 2
        assert all(auth_session.revoked_at is None for auth_session in auth_sessions)

    response = client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        auth_sessions = session.scalars(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        ).all()

        assert len(auth_sessions) == 2
        assert all(
            auth_session.revoked_at is not None for auth_session in auth_sessions
        )


def test_logout_all_does_not_revoke_other_users_sessions(
    client,
    regular_user,
    admin_user,
):
    regular_login = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert regular_login.status_code == 200

    regular_access_token = regular_login.get_json()["access_token"]

    admin_login = client.post(
        "/api/auth/login",
        json=admin_user,
    )

    assert admin_login.status_code == 200

    response = client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {regular_access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        regular_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        admin = UserRepository(session).get_by_email(admin_user["email"])

        assert admin is not None

        admin_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == admin.id)
        )

        assert regular_session is not None
        assert admin_session is not None

        assert regular_session.revoked_at is not None
        assert admin_session.revoked_at is None


def test_logout_all_requires_fresh_token(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert csrf_cookie is not None

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert refresh_response.status_code == 200

    non_fresh_access_token = refresh_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {non_fresh_access_token}"},
    )

    assert response.status_code == 401


def test_logout_all_revoked_refresh_token_cannot_refresh(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    refresh_cookie = client.get_cookie(
        "refresh_token_cookie",
        path="/api/auth",
    )

    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert refresh_cookie is not None
    assert csrf_cookie is not None

    logout_response = client.post(
        "/api/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert logout_response.status_code == 200

    # Restore the refresh token that the route removed from the browser.
    # This proves server-side revocation still prevents its use.
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
    assert refresh_response.get_json()["message"] == "Refresh session revoked."


def test_change_email(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-email",
        json={
            "new_email": "newjohn@example.com",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Email changed successfully."

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None
        assert user.email == "newjohn@example.com"


def test_change_email_rejects_existing_email(
    client,
    regular_user,
    admin_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-email",
        json={
            "new_email": admin_user["email"],
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Email already exists."


def test_change_email_requires_fresh_token(client, regular_user):
    client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    csrf_cookie = client.get_cookie("csrf_refresh_token")
    assert csrf_cookie is not None

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={"X-CSRF-TOKEN": csrf_cookie.value},
    )

    assert refresh_response.status_code == 200

    non_fresh_token = refresh_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-email",
        json={
            "current_password": regular_user["password"],
            "new_email": "newjohn@example.com",
        },
        headers={"Authorization": f"Bearer {non_fresh_token}"},
    )

    assert response.status_code == 401


def test_change_email_rejects_invalid_email(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-email",
        json={
            "new_email": "not-an-email",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "errors" in data
    assert "new_email" in data["errors"]


def test_change_email_revokes_refresh_sessions(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is None

    response = client.post(
        "/api/auth/change-email",
        json={
            "new_email": "newjohn@example.com",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_change_email_to_same_email_is_noop(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        sid = auth_session.id

    response = client.post(
        "/api/auth/change-email",
        json={
            "new_email": regular_user["email"],
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        auth_session = session.get(AuthSession, sid)

        assert auth_session is not None
        assert auth_session.revoked_at is None


def test_change_password(client, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "new_password": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Password changed successfully."

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None
        assert check_password_hash(
            user.password_hash,
            "NewPassword123!",
        )


def test_reauthenticate_rejects_wrong_password(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/reauthenticate",
        json={
            "current_password": "WrongPassword123!",
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid password."


def test_change_password_revokes_all_refresh_sessions(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is None

    response = client.post(
        "/api/auth/change-password",
        json={
            "new_password": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

    with SessionLocal() as session:
        auth_session = session.scalar(
            select(AuthSession).where(AuthSession.user_id == regular_user["id"])
        )

        assert auth_session is not None
        assert auth_session.revoked_at is not None


def test_change_password_requires_fresh_token(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert login_response.status_code == 200

    csrf_cookie = client.get_cookie("csrf_refresh_token")

    assert csrf_cookie is not None

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={
            "X-CSRF-TOKEN": csrf_cookie.value,
        },
    )

    assert refresh_response.status_code == 200

    non_fresh_access_token = refresh_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "new_password": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {non_fresh_access_token}"},
    )

    assert response.status_code == 401


def test_change_password_requires_minimum_password_length(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    response = client.post(
        "/api/auth/change-password",
        json={
            "new_password": "short",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "errors" in data
    assert "new_password" in data["errors"]


def test_old_password_no_longer_works_after_change(
    client,
    regular_user,
):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    access_token = login_response.get_json()["access_token"]

    change_response = client.post(
        "/api/auth/change-password",
        json={
            "new_password": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert change_response.status_code == 200

    old_password_login = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": regular_user["password"],
        },
    )

    assert old_password_login.status_code == 401

    new_password_login = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": "NewPassword123!",
        },
    )

    assert new_password_login.status_code == 200


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
