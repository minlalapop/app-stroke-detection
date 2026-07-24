from fastapi.testclient import TestClient


def login_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_default_admin_can_login_and_read_profile(client: TestClient) -> None:
    headers = login_admin(client)
    profile = client.get("/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["username"] == "admin"
    assert profile.json()["role"] == "admin"


def test_register_creates_doctor_without_password_in_response(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "dr.amal",
            "full_name": "Dr Amal Idrissi",
            "password": "safe-password",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "doctor"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_doctor_registers_and_logs_in_with_email(client: TestClient) -> None:
    registered = client.post(
        "/auth/register",
        json={
            "email": "doctor@example.com",
            "full_name": "Doctor Example",
            "password": "doctor-password",
        },
    )
    assert registered.status_code == 201
    assert registered.json()["email"] == "doctor@example.com"

    login = client.post(
        "/auth/login",
        json={"email": "doctor@example.com", "password": "doctor-password"},
    )
    assert login.status_code == 200


def test_doctor_cannot_list_users(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "username": "doctor",
            "full_name": "Doctor Test",
            "password": "doctor-password",
        },
    )
    token = client.post(
        "/auth/login", json={"username": "doctor", "password": "doctor-password"}
    ).json()["access_token"]
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_logout_invalidates_token(client: TestClient) -> None:
    headers = login_admin(client)
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_admin_can_create_and_disable_user(client: TestClient) -> None:
    headers = login_admin(client)
    created = client.post(
        "/users",
        headers=headers,
        json={
            "username": "second.doctor",
            "full_name": "Second Doctor",
            "password": "second-password",
            "role": "doctor",
            "is_active": True,
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    disabled = client.put(
        f"/users/{user_id}", headers=headers, json={"is_active": False}
    )
    assert disabled.status_code == 200
    assert disabled.json()["is_active"] is False
