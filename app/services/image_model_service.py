from collections.abc import Callable
from pathlib import Path

from app.services.model_common import ModelExecutionStatus

ImageSegmenter = Callable[[str], dict]


class ImageModelService:
    """Boundary for the future image segmentation adapter.

    DICOM conversion, tensor preparation and post-processing are deliberately left
    to the future adapter because those rules must come from the trained model.
    """

    def __init__(
        self,
        model_path: str | None = None,
        segmenter: ImageSegmenter | None = None,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.segmenter = segmenter

    def is_available(self) -> bool:
        return bool(
            self.model_path
            and self.model_path.is_file()
            and self.segmenter is not None
        )

    def status(self) -> ModelExecutionStatus:
        if self.is_available():
            return ModelExecutionStatus.READY
        return ModelExecutionStatus.MODEL_NOT_AVAILABLE

    def segment(self, dicom_study_id: str) -> dict:
        if not self.is_available():
            return {
                "status": ModelExecutionStatus.MODEL_NOT_AVAILABLE,
                "lesion_detected": None,
                "lesion_volume_ml": None,
                "mask_uri": None,
                "preview_uri": None,
                "model_version": None,
                "error_message": "Image model is not available",
            }
        try:
            result = self.segmenter(dicom_study_id)  # type: ignore[misc]
            return {**result, "status": ModelExecutionStatus.COMPLETED}
        except Exception:
            return {
                "status": ModelExecutionStatus.FAILED,
                "lesion_detected": None,
                "lesion_volume_ml": None,
                "mask_uri": None,
                "preview_uri": None,
                "model_version": None,
                "error_message": "Image model execution failed",
            }
