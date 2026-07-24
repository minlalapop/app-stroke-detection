import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.prediction import ModelResultStatus


class ReportStatus(str, enum.Enum):
    READY_FOR_EXPORT = "READY_FOR_EXPORT"
    LLM_DRAFT_REVIEW_REQUIRED = "LLM_DRAFT_REVIEW_REQUIRED"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    deterministic_report_uri: Mapped[str] = mapped_column(String(1000))
    deterministic_sha256: Mapped[str] = mapped_column(String(64))
    llm_status: Mapped[ModelResultStatus] = mapped_column(
        Enum(
            ModelResultStatus,
            name="model_result_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    llm_enriched_report_uri: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(
            ReportStatus,
            name="report_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    llm_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    llm_approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
