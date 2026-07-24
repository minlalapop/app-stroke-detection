import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExportFormat(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"


class ExportSource(str, enum.Enum):
    DETERMINISTIC = "DETERMINISTIC"
    DETERMINISTIC_WITH_APPROVED_LLM = "DETERMINISTIC_WITH_APPROVED_LLM"


class ReportExport(Base):
    __tablename__ = "report_exports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    format: Mapped[ExportFormat] = mapped_column(
        Enum(
            ExportFormat,
            name="export_format",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    source: Mapped[ExportSource] = mapped_column(
        Enum(
            ExportSource,
            name="export_source",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    file_uri: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64))
    generated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
