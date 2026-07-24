import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.imaging_study import ImagingStudyStatus


class ImagingStudyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    modality: str
    original_filename: str
    original_file_uri: str
    sha256: str
    file_size: int
    metadata_json: dict
    status: ImagingStudyStatus
    created_at: datetime
