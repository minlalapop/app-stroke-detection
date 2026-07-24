import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.prediction import ModelResultStatus
from app.models.report import ReportStatus


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    deterministic_report_uri: str
    deterministic_sha256: str
    llm_status: ModelResultStatus
    llm_enriched_report_uri: str | None
    status: ReportStatus
    generated_by: uuid.UUID
    generated_at: datetime
    llm_approved_by: uuid.UUID | None
    llm_approved_at: datetime | None
