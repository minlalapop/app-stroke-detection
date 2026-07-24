from fastapi.testclient import TestClient


PATIENT = {
    "first_name": "Nadia",
    "last_name": "Alaoui",
    "birth_date": "1968-09-03",
    "sex": "female",
}

CLINICAL_DATA = {
    "age": 57,
    "hypertension": True,
    "heart_disease": False,
    "ever_married": "Yes",
    "work_type": "Private",
    "residence_type": "Urban",
    "avg_glucose_level": 118.4,
    "bmi": 26.2,
    "smoking_status": "never smoked",
}


def authenticated_headers(client: TestClient) -> dict[str, str]:
    client.post(
        "/auth/register",
        json={
            "username": "clinical.doctor",
            "full_name": "Clinical Doctor",
            "password": "doctor-password",
        },
    )
    token = client.post(
        "/auth/login",
        json={"username": "clinical.doctor", "password": "doctor-password"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_patient(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/patients", json=PATIENT, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_list_clinical_data(client: TestClient) -> None:
    headers = authenticated_headers(client)
    patient_id = create_patient(client, headers)

    created = client.post(
        f"/patients/{patient_id}/clinical-data",
        json=CLINICAL_DATA,
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["patient_id"] == patient_id
    assert created.json()["avg_glucose_level"] == 118.4

    listed = client.get(
        f"/patients/{patient_id}/clinical-data", headers=headers
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]

    fetched = client.get(
        f"/patients/{patient_id}/clinical-data/{created.json()['id']}",
        headers=headers,
    )
    assert fetched.status_code == 200

    updated = client.put(
        f"/patients/{patient_id}/clinical-data/{created.json()['id']}",
        json={**CLINICAL_DATA, "bmi": 25.8},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["bmi"] == 25.8


def test_accepts_partial_clinical_data_without_inventing_values(client: TestClient) -> None:
    headers = authenticated_headers(client)
    patient_id = create_patient(client, headers)
    created = client.post(
        f"/patients/{patient_id}/clinical-data",
        json={"hypertension": False},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["hypertension"] is False
    assert created.json()["bmi"] is None
    assert created.json()["smoking_status"] is None


def test_clinical_data_requires_existing_patient(client: TestClient) -> None:
    response = client.post(
        "/patients/00000000-0000-0000-0000-000000000000/clinical-data",
        json=CLINICAL_DATA,
        headers=authenticated_headers(client),
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Patient not found"}


def test_clinical_record_must_belong_to_patient(client: TestClient) -> None:
    headers = authenticated_headers(client)
    first_patient = create_patient(client, headers)
    record = client.post(
        f"/patients/{first_patient}/clinical-data",
        json=CLINICAL_DATA,
        headers=headers,
    ).json()
    second_patient = client.post(
        "/patients",
        json={**PATIENT, "first_name": "Other"},
        headers=headers,
    ).json()["id"]
    response = client.get(
        f"/patients/{second_patient}/clinical-data/{record['id']}", headers=headers
    )
    assert response.status_code == 404


def test_clinical_data_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/patients/00000000-0000-0000-0000-000000000000/clinical-data"
    )
    assert response.status_code == 401


def test_reject_negative_numeric_values(client: TestClient) -> None:
    headers = authenticated_headers(client)
    patient_id = create_patient(client, headers)
    response = client.post(
        f"/patients/{patient_id}/clinical-data",
        json={"avg_glucose_level": -1},
        headers=headers,
    )
    assert response.status_code == 422


def test_rejects_stroke_target_as_clinical_input(client: TestClient) -> None:
    headers = authenticated_headers(client)
    patient_id = create_patient(client, headers)
    response = client.post(
        f"/patients/{patient_id}/clinical-data",
        json={**CLINICAL_DATA, "stroke": 1},
        headers=headers,
    )
    assert response.status_code == 422
