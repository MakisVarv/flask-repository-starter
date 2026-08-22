from app.config.database import SessionLocal
from app.users import UserRepository


def get_admin_token(client, admin_user):
    response = client.post(
        "/api/auth/login",
        json=admin_user,
    )

    assert response.status_code == 200

    return response.get_json()["access_token"]


def test_user_read(client, admin_user, regular_user):
    login_response = client.post(
        "/api/auth/login",
        json=admin_user,
    )
    data = login_response.get_json()
    assert login_response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    access_token = data["access_token"]
    user_id = regular_user["id"]
    second_response = client.get(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user_data = second_response.get_json()
    assert user_data is not None
    assert second_response.status_code == 200
    assert user_data["id"] == str(regular_user["id"])
    assert user_data["email"] == "john@example.com"


def test_no_user_read(client, regular_user):
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
    access_token = data["access_token"]
    user_id = regular_user["id"]
    second_response = client.get(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response_data = second_response.get_json()
    assert second_response.status_code == 403
    assert (
        response_data["message"] == "You do not have permission to perform this action."
    )


def test_unknown_user_read(client, admin_user):
    login_response = client.post(
        "/api/auth/login",
        json=admin_user,
    )
    data = login_response.get_json()
    assert login_response.status_code == 200
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    access_token = data["access_token"]
    user_id = "00000000-0000-0000-0000-000000000001"
    second_response = client.get(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response_data = second_response.get_json()
    assert second_response.status_code == 404
    assert response_data["message"] == "User not found."


def test_admin_can_create_user(client, admin_user, user_role):
    login_response = client.post(
        "/api/auth/login",
        json=admin_user,
    )
    assert login_response.status_code == 200
    access_token = login_response.get_json()["access_token"]

    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "password": "Password123!",
        "role_id": str(user_role),
    }

    response = client.post(
        "/api/users/",
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["email"] == "jane@example.com"
    assert data["role"]["id"] == str(user_role)
    assert "password" not in data
    assert "password_hash" not in data
    with SessionLocal() as session:
        user_repository = UserRepository(session)
        created_user = user_repository.get_by_email("jane@example.com")

        assert created_user is not None
        assert created_user.first_name == "Jane"
        assert created_user.role_id == user_role


def test_regular_user_cannot_create_user(client, regular_user, user_role):
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

    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "password": "Password123!",
        "role_id": str(user_role),
    }

    response = client.post(
        "/api/users/",
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    data = response.get_json()

    assert response.status_code == 403
    assert data["message"] == "You do not have permission to perform this action."

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        created_user = user_repository.get_by_email("jane@example.com")

        assert created_user is None


def test_users_pagination(client, admin_user, regular_user):
    access_token = get_admin_token(client, admin_user)

    response = client.get(
        "/api/users/?page=1&page_size=1",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 200
    assert len(data["items"]) == 1

    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 1
    assert data["pagination"]["total"] == 2
    assert data["pagination"]["total_pages"] == 2


def test_users_search(client, admin_user, regular_user):
    access_token = get_admin_token(client, admin_user)

    response = client.get(
        "/api/users/?search=john",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 200

    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == regular_user["email"]

    assert data["pagination"]["total"] == 1
    assert data["pagination"]["total_pages"] == 1


def test_users_filter_by_role(client, admin_user, regular_user):
    access_token = get_admin_token(client, admin_user)

    response = client.get(
        "/api/users/?role=User",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 200

    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == regular_user["email"]
    assert data["items"][0]["role"]["name"] == "User"

    assert data["pagination"]["total"] == 1


def test_users_filter_inactive(client, admin_user, regular_user):
    access_token = get_admin_token(client, admin_user)

    with SessionLocal() as session:
        user_repository = UserRepository(session)
        user = user_repository.get_by_id(regular_user["id"])

        assert user is not None

        user.is_active = False
        session.commit()

    response = client.get(
        "/api/users/?is_active=false",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 200

    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == regular_user["email"]
    assert data["items"][0]["is_active"] is False

    assert data["pagination"]["total"] == 1


def test_users_reject_invalid_page_size(client, admin_user):
    access_token = get_admin_token(client, admin_user)

    response = client.get(
        "/api/users/?page_size=101",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.get_json()

    assert response.status_code == 400
    assert "errors" in data
    assert "page_size" in data["errors"]
