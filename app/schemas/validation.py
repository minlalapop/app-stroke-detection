import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.validation import ValidationStatus


class DoctorValidationCreate(BaseModel):
    validation_status: ValidationStatus
    comment: str | None = Field(default=None, max_length=2000)


class DoctorValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    doctor_id: uuid.UUID
    validation_status: ValidationStatus
    comment: str | None
    validated_at: datetime
