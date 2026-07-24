import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClinicalDataCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: float | None = Field(default=None, ge=0)
    hypertension: bool | None = None
    heart_disease: bool | None = None
    ever_married: Literal["Yes", "No"] | None = None
    work_type: Literal[
        "Private", "Self-employed", "children", "Govt_job", "Never_worked"
    ] | None = None
    residence_type: Literal["Urban", "Rural"] | None = None
    avg_glucose_level: float | None = Field(default=None, ge=0)
    bmi: float | None = Field(default=None, ge=0)
    smoking_status: str | None = Field(default=None, max_length=100)

    @field_validator("smoking_status")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        allowed = {"never smoked", "Unknown", "formerly smoked", "smokes"}
        if value not in allowed:
            raise ValueError("invalid smoking status")
        return value


class ClinicalDataRead(ClinicalDataCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    patient_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
