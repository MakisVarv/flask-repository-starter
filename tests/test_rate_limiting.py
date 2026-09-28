def test_forgot_password_email_limit_survives_ip_rotation(client):
    email = "target@example.com"

    for attempt in range(1, 11):
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": email},
            environ_overrides={
                "REMOTE_ADDR": f"203.0.113.{attempt}",
            },
        )

        assert response.status_code == 200

    blocked_response = client.post(
        "/api/auth/forgot-password",
        json={"email": email},
        environ_overrides={
            "REMOTE_ADDR": "203.0.113.11",
        },
    )

    assert blocked_response.status_code == 429


def test_login_email_limit_survives_ip_rotation(client, regular_user):
    for attempt in range(1, 11):
        response = client.post(
            "/api/auth/login",
            json={
                "email": regular_user["email"],
                "password": "WrongPassword123!",
            },
            environ_overrides={
                "REMOTE_ADDR": f"203.0.113.{attempt}",
            },
        )

        assert response.status_code == 401

    blocked_response = client.post(
        "/api/auth/login",
        json={
            "email": regular_user["email"],
            "password": "WrongPassword123!",
        },
        environ_overrides={
            "REMOTE_ADDR": "203.0.113.11",
        },
    )

    assert blocked_response.status_code == 429


def test_login_ip_limit_survives_email_rotation(client):
    ip_address = "203.0.113.50"

    for attempt in range(1, 6):
        response = client.post(
            "/api/auth/login",
            json={
                "email": f"target{attempt}@example.com",
                "password": "WrongPassword123!",
            },
            environ_overrides={
                "REMOTE_ADDR": ip_address,
            },
        )

        assert response.status_code == 401

    blocked_response = client.post(
        "/api/auth/login",
        json={
            "email": "target6@example.com",
            "password": "WrongPassword123!",
        },
        environ_overrides={
            "REMOTE_ADDR": ip_address,
        },
    )

    assert blocked_response.status_code == 429
