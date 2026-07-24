from pathlib import Path

from fastapi.testclient import TestClient

from app.services.image_model_service import ImageModelService
from app.services.model_common import ModelExecutionStatus
from app.services.tabular_model_service import TabularModelService


def test_catboost_columns_keep_target_separate() -> None:
    assert TabularModelService.FEATURE_NAMES == (
        "gender",
        "age",
        "hypertension",
        "heart_disease",
        "ever_married",
        "work_type",
        "Residence_type",
        "avg_glucose_level",
        "bmi",
        "smoking_status",
    )
    assert TabularModelService.TARGET_NAME == "stroke"
    assert "stroke" not in TabularModelService.FEATURE_NAMES


def test_models_return_not_available_without_artifacts() -> None:
    tabular = TabularModelService()
    image = ImageModelService()

    tabular_result = tabular.predict({"age": 70})
    image_result = image.segment("study-id")

    assert tabular_result["status"] == ModelExecutionStatus.MODEL_NOT_AVAILABLE
    assert tabular_result["risk_score"] is None
    assert image_result["status"] == ModelExecutionStatus.MODEL_NOT_AVAILABLE
    assert image_result["mask_uri"] is None


def test_file_alone_does_not_make_model_available(tmp_path: Path) -> None:
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(b"model-placeholder")
    assert TabularModelService(model_path=str(artifact)).is_available() is False
    assert ImageModelService(model_path=str(artifact)).is_available() is False


def test_injected_real_adapters_are_executed(tmp_path: Path) -> None:
    tabular_artifact = tmp_path / "tabular.model"
    image_artifact = tmp_path / "image.model"
    tabular_artifact.write_bytes(b"real-model-content-later")
    image_artifact.write_bytes(b"real-model-content-later")

    tabular = TabularModelService(
        str(tabular_artifact),
        predictor=lambda data: {
            "risk_score": 0.2,
            "risk_label": None,
            "model_version": "test-tabular",
            "received": data,
        },
    )
    image = ImageModelService(
        str(image_artifact),
        segmenter=lambda study_id: {
            "lesion_detected": False,
            "lesion_volume_ml": 0.0,
            "mask_uri": "local://test-mask",
            "preview_uri": None,
            "model_version": "test-image",
            "received": study_id,
        },
    )

    assert tabular.predict({"age": 70})["received"] == {"age": 70}
    assert image.segment("study-id")["received"] == "study-id"


def test_model_status_endpoint_requires_authentication(client: TestClient) -> None:
    assert client.get("/models/status").status_code == 401

    login = client.post(
        "/auth/login", json={"username": "admin", "password": "admin123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = client.get("/models/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "tabular_model": {"available": False, "status": "MODEL_NOT_AVAILABLE"},
        "image_model": {"available": False, "status": "MODEL_NOT_AVAILABLE"},
    }
