from collections.abc import Callable
from pathlib import Path

from app.services.model_common import ModelExecutionStatus

TabularPredictor = Callable[[dict], dict]


class TabularModelService:
    """Boundary for the future CatBoost adapter.

    No feature transformation or medical threshold is defined here. The future
    adapter must receive the clinical values as stored and return real model output.
    """

    FEATURE_NAMES = (
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
    TARGET_NAME = "stroke"

    def __init__(
        self,
        model_path: str | None = None,
        predictor: TabularPredictor | None = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.predictor = predictor

    def is_available(self) -> bool:
        return bool(
            self.model_path
            and self.model_path.is_file()
            and self.predictor is not None
        )

    def status(self) -> ModelExecutionStatus:
        if self.is_available():
            return ModelExecutionStatus.READY
        return ModelExecutionStatus.MODEL_NOT_AVAILABLE

    def predict(self, clinical_data: dict) -> dict:
        if not self.is_available():
            return {
                "status": ModelExecutionStatus.MODEL_NOT_AVAILABLE,
                "risk_score": None,
                "risk_label": None,
                "model_version": None,
                "error_message": "Tabular model is not available",
            }
        try:
            result = self.predictor(clinical_data)  # type: ignore[misc]
            return {**result, "status": ModelExecutionStatus.COMPLETED}
        except Exception:
            return {
                "status": ModelExecutionStatus.FAILED,
                "risk_score": None,
                "risk_label": None,
                "model_version": None,
                "error_message": "Tabular model execution failed",
            }
