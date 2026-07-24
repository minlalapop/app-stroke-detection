import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientFields(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    birth_date: date
    sex: Literal["Female", "Male"]

    @field_validator("sex", mode="before")
    @classmethod
    def normalize_sex(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        return {
            "f": "Female",
            "female": "Female",
            "m": "Male",
            "male": "Male",
        }.get(normalized, value)

    @field_validator("first_name", "last_name")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("birth_date")
    @classmethod
    def reject_future_birth_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("birth date cannot be in the future")
        return value


class PatientCreate(PatientFields):
    pass


class PatientUpdate(PatientFields):
    pass


class PatientRead(PatientFields):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
