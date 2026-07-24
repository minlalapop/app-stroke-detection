import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.analysis import AnalysisStatus
from app.models.prediction import ModelResultStatus


class AnalysisCreate(BaseModel):
    patient_id: uuid.UUID
    clinical_data_id: uuid.UUID | None = None
    imaging_study_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def require_input(self):
        if self.clinical_data_id is None and self.imaging_study_id is None:
            raise ValueError("clinical_data_id or imaging_study_id is required")
        return self


class TabularPredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ModelResultStatus
    risk_score: float | None
    risk_label: str | None
    model_version: str | None
    error_message: str | None
    created_at: datetime


class ImageSegmentationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ModelResultStatus
    lesion_detected: bool | None
    lesion_volume_ml: float | None
    mask_uri: str | None
    preview_uri: str | None
    model_version: str | None
    error_message: str | None
    created_at: datetime


class AnalysisRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    clinical_data_id: uuid.UUID | None
    imaging_study_id: uuid.UUID | None
    status: AnalysisStatus
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    tabular_result: TabularPredictionRead | None = None
    imaging_result: ImageSegmentationRead | None = None
