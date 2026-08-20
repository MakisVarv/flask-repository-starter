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
    assert second_response.status_code == 200
    assert user_data["id"] == str(regular_user["id"])
    assert user_data is not None
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
