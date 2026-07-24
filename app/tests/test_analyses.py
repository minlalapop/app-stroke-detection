from fastapi.testclient import TestClient


def headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_patient(client: TestClient, auth: dict[str, str], first_name: str) -> str:
    response = client.post(
        "/patients",
        headers=auth,
        json={
            "first_name": first_name,
            "last_name": "Analysis",
            "birth_date": "1970-01-01",
            "sex": "female",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_clinical_data(client: TestClient, auth: dict[str, str], patient: str) -> str:
    response = client.post(
        f"/patients/{patient}/clinical-data",
        headers=auth,
        json={
            "age": 56,
            "hypertension": True,
            "heart_disease": False,
            "ever_married": "Yes",
            "work_type": "Private",
            "residence_type": "Urban",
            "avg_glucose_level": 110.0,
            "bmi": 25.0,
            "smoking_status": None,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_and_run_analysis_when_model_is_unavailable(client: TestClient) -> None:
    auth = headers(client)
    patient = create_patient(client, auth, "Sara")
    clinical = create_clinical_data(client, auth, patient)

    created = client.post(
        "/analyses",
        headers=auth,
        json={"patient_id": patient, "clinical_data_id": clinical},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "READY"
    assert created.json()["tabular_result"] is None

    analysis_id = created.json()["id"]
    run = client.post(f"/analyses/{analysis_id}/run", headers=auth)
    assert run.status_code == 200
    result = run.json()
    assert result["status"] == "MODEL_NOT_AVAILABLE"
    assert result["tabular_result"]["status"] == "MODEL_NOT_AVAILABLE"
    assert result["tabular_result"]["risk_score"] is None
    assert result["imaging_result"] is None

    fetched = client.get(f"/analyses/{analysis_id}", headers=auth)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == result["id"]
    assert fetched.json()["tabular_result"] == result["tabular_result"]
    listed = client.get(f"/patients/{patient}/analyses", headers=auth)
    assert [item["id"] for item in listed.json()] == [analysis_id]


def test_analysis_rejects_input_from_another_patient(client: TestClient) -> None:
    auth = headers(client)
    first_patient = create_patient(client, auth, "First")
    second_patient = create_patient(client, auth, "Second")
    clinical = create_clinical_data(client, auth, first_patient)
    response = client.post(
        "/analyses",
        headers=auth,
        json={"patient_id": second_patient, "clinical_data_id": clinical},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Clinical data does not belong to patient"}


def test_analysis_requires_at_least_one_input(client: TestClient) -> None:
    auth = headers(client)
    patient = create_patient(client, auth, "NoInput")
    response = client.post("/analyses", headers=auth, json={"patient_id": patient})
    assert response.status_code == 422


def test_analysis_cannot_be_run_twice(client: TestClient) -> None:
    auth = headers(client)
    patient = create_patient(client, auth, "Once")
    clinical = create_clinical_data(client, auth, patient)
    analysis_id = client.post(
        "/analyses",
        headers=auth,
        json={"patient_id": patient, "clinical_data_id": clinical},
    ).json()["id"]
    assert client.post(f"/analyses/{analysis_id}/run", headers=auth).status_code == 200
    assert client.post(f"/analyses/{analysis_id}/run", headers=auth).status_code == 409


def test_analysis_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/analyses/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 401
