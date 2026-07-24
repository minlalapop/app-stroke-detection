import json

from fastapi.testclient import TestClient

from app.api.reports import get_llm_enrichment_service
from app.main import app
from app.services.llm_enrichment_service import LLMEnrichmentService
from app.storage.file_storage import LocalFileStorage, get_file_storage


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_doctor(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "username": "report.doctor",
            "full_name": "Dr Report",
            "password": "doctor-password",
        },
    )
    assert response.status_code == 201
    return login(client, "report.doctor", "doctor-password")


def completed_unavailable_analysis(client: TestClient, auth: dict[str, str]) -> str:
    patient = client.post(
        "/patients",
        headers=auth,
        json={
            "first_name": "Report",
            "last_name": "Patient",
            "birth_date": "1960-05-04",
            "sex": "female",
        },
    ).json()
    clinical = client.post(
        f"/patients/{patient['id']}/clinical-data",
        headers=auth,
        json={"age": 66, "hypertension": True},
    ).json()
    analysis = client.post(
        "/analyses",
        headers=auth,
        json={"patient_id": patient["id"], "clinical_data_id": clinical["id"]},
    ).json()
    run = client.post(f"/analyses/{analysis['id']}/run", headers=auth)
    assert run.status_code == 200
    return analysis["id"]


def test_report_is_blocked_before_doctor_validation(client: TestClient, tmp_path) -> None:
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(root=tmp_path)
    admin = login(client, "admin", "admin123")
    analysis_id = completed_unavailable_analysis(client, admin)
    response = client.post(f"/analyses/{analysis_id}/report", headers=admin)
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Report cannot be generated before doctor validation."
    }
    assert not list(tmp_path.rglob("report*"))


def test_validated_deterministic_report_works_without_llm(client: TestClient, tmp_path) -> None:
    app.dependency_overrides[get_file_storage] = lambda: LocalFileStorage(root=tmp_path)
    admin = login(client, "admin", "admin123")
    analysis_id = completed_unavailable_analysis(client, admin)
    doctor = create_doctor(client)
    validation = client.post(
        f"/analyses/{analysis_id}/validate",
        headers=doctor,
        json={"validation_status": "VALIDATED", "comment": "Résultats vérifiés."},
    )
    assert validation.status_code == 201

    generated = client.post(f"/analyses/{analysis_id}/report", headers=doctor)
    assert generated.status_code == 201
    report = generated.json()
    assert report["llm_status"] == "MODEL_NOT_AVAILABLE"
    assert report["status"] == "READY_FOR_EXPORT"
    assert report["llm_enriched_report_uri"] is None

    report_file = next(tmp_path.rglob("report.json"))
    data = json.loads(report_file.read_text())
    assert data["doctor_validation"]["status"] == "VALIDATED"
    assert data["doctor_validation"]["doctor_name"] == "Dr Report"
    assert data["tabular_result"]["risk_score"] is None
    assert "Ne remplace pas l’avis médical." in data["limitations"]


def test_llm_enrichment_is_separate_and_requires_doctor_approval(
    client: TestClient, tmp_path
) -> None:
    storage = LocalFileStorage(root=tmp_path)
    artifact = tmp_path / "llm.model"
    artifact.write_bytes(b"future-local-llm")
    app.dependency_overrides[get_file_storage] = lambda: storage
    app.dependency_overrides[get_llm_enrichment_service] = lambda: LLMEnrichmentService(
        str(artifact), enhancer=lambda report: "Synthèse enrichie fondée sur le rapport."
    )
    admin = login(client, "admin", "admin123")
    analysis_id = completed_unavailable_analysis(client, admin)
    doctor = create_doctor(client)
    client.post(
        f"/analyses/{analysis_id}/validate",
        headers=doctor,
        json={"validation_status": "VALIDATED", "comment": None},
    )
    report = client.post(f"/analyses/{analysis_id}/report", headers=doctor).json()
    assert report["status"] == "LLM_DRAFT_REVIEW_REQUIRED"
    assert report["llm_status"] == "COMPLETED"
    assert report["llm_enriched_report_uri"] != report["deterministic_report_uri"]
    draft = next(tmp_path.rglob("*.llm-draft.txt")).read_text()
    assert draft.startswith("BROUILLON ENRICHI PAR LLM")

    approved = client.post(
        f"/reports/{report['id']}/approve-llm", headers=doctor
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "READY_FOR_EXPORT"
    assert approved.json()["llm_approved_by"] is not None
