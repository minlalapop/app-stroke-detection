import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalysisStatus(str, enum.Enum):
    CREATED = "CREATED"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    READY = "READY"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL_COMPLETED = "PARTIAL_COMPLETED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    FAILED = "FAILED"
    VALIDATED_BY_DOCTOR = "VALIDATED_BY_DOCTOR"
    REPORT_GENERATED = "REPORT_GENERATED"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    clinical_data_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("clinical_data.id", ondelete="SET NULL"), nullable=True
    )
    imaging_study_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("imaging_studies.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(
            AnalysisStatus,
            name="analysis_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
