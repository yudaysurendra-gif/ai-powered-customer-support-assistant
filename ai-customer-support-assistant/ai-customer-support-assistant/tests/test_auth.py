def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


def test_register_duplicate_email_fails(client):
    payload = {"email": "dup@example.com", "full_name": "Dup User", "password": "SecurePass123!"}
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    assert second.status_code == 400


def test_login_success(client):
    payload = {"email": "loginuser@example.com", "full_name": "Login User", "password": "SecurePass123!"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    payload = {"email": "wrongpass@example.com", "full_name": "User", "password": "SecurePass123!"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": "WrongPassword"},
    )
    assert response.status_code == 401
