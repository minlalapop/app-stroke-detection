from fastapi.testclient import TestClient


PATIENT = {
    "first_name": "Amina",
    "last_name": "Bennani",
    "birth_date": "1975-04-12",
    "sex": "female",
}


def doctor_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "username": "patient.doctor",
            "full_name": "Patient Doctor",
            "password": "doctor-password",
        },
    )
    token = client.post(
        "/auth/login",
        json={"username": "patient.doctor", "password": "doctor-password"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_and_get_patient(client: TestClient) -> None:
    headers = doctor_headers(client)
    created = client.post("/patients", json=PATIENT, headers=headers)
    assert created.status_code == 201
    patient = created.json()
    assert patient["first_name"] == "Amina"
    assert patient["id"]

    fetched = client.get(f"/patients/{patient['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json() == patient


def test_accept_legacy_abbreviated_patient_sex(client: TestClient) -> None:
    headers = doctor_headers(client)
    created = client.post(
        "/patients",
        json={**PATIENT, "sex": "f"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["sex"] == "Female"


def test_list_and_update_patient(client: TestClient) -> None:
    headers = doctor_headers(client)
    patient_id = client.post("/patients", json=PATIENT, headers=headers).json()["id"]
    updated_payload = {**PATIENT, "last_name": "El Amrani"}

    updated = client.put(f"/patients/{patient_id}", json=updated_payload, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["last_name"] == "El Amrani"

    listed = client.get("/patients", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [patient_id]


def test_delete_patient(client: TestClient) -> None:
    headers = doctor_headers(client)
    patient_id = client.post("/patients", json=PATIENT, headers=headers).json()["id"]

    deleted = client.delete(f"/patients/{patient_id}", headers=headers)

    assert deleted.status_code == 204
    assert client.get(f"/patients/{patient_id}", headers=headers).status_code == 404


def test_patient_not_found(client: TestClient) -> None:
    headers = doctor_headers(client)
    response = client.get(
        "/patients/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Patient not found"}


def test_reject_blank_patient_name(client: TestClient) -> None:
    response = client.post(
        "/patients",
        json={**PATIENT, "first_name": "   "},
        headers=doctor_headers(client),
    )
    assert response.status_code == 422


def test_patient_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/patients").status_code == 401
    assert client.post("/patients", json=PATIENT).status_code == 401


def test_reject_future_birth_date(client: TestClient) -> None:
    response = client.post(
        "/patients",
        json={**PATIENT, "birth_date": "2999-01-01"},
        headers=doctor_headers(client),
    )
    assert response.status_code == 422
