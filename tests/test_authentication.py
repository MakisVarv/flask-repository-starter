def test_users_requires_authentication(client):
    response = client.get("/api/users/")

    assert response.status_code == 401
