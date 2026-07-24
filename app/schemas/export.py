import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.export import ExportFormat, ExportSource


class ReportExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    format: ExportFormat
    source: ExportSource
    file_uri: str
    sha256: str
    generated_by: uuid.UUID
    generated_at: datetime
