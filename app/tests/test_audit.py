from fastapi.testclient import TestClient


def test_admin_can_read_important_audit_events(client: TestClient) -> None:
    login = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    patient = client.post(
        "/patients",
        headers=headers,
        json={
            "first_name": "Audit",
            "last_name": "Patient",
            "birth_date": "1985-01-01",
            "sex": "female",
        },
    )
    assert patient.status_code == 201

    events = client.get("/audit-events", headers=headers)
    assert events.status_code == 200
    actions = {event["action"] for event in events.json()}
    assert "LOGIN_SUCCEEDED" in actions
    assert "PATIENT_CREATED" in actions
    patient_event = next(
        event for event in events.json() if event["action"] == "PATIENT_CREATED"
    )
    assert patient_event["entity_id"] == patient.json()["id"]
    assert patient_event["details_json"] == {}


def test_doctor_cannot_read_audit_events(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={
            "username": "audit.doctor",
            "full_name": "Audit Doctor",
            "password": "doctor-password",
        },
    )
    login = client.post(
        "/auth/login",
        json={"username": "audit.doctor", "password": "doctor-password"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/audit-events", headers=headers).status_code == 403


def test_failed_login_is_audited_without_password(client: TestClient) -> None:
    failed = client.post(
        "/auth/login", json={"username": "unknown", "password": "not-recorded"}
    )
    assert failed.status_code == 401
    admin = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {admin.json()['access_token']}"}
    event = next(
        item
        for item in client.get("/audit-events", headers=headers).json()
        if item["action"] == "LOGIN_FAILED"
    )
    assert event["details_json"] == {"username": "unknown"}
    assert "password" not in event["details_json"]
