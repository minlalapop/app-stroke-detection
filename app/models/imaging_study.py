import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImagingStudyStatus(str, enum.Enum):
    UPLOADED = "uploaded"


class ImagingStudy(Base):
    __tablename__ = "imaging_studies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    modality: Mapped[str] = mapped_column(String(50))
    original_filename: Mapped[str] = mapped_column(String(255))
    original_file_uri: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64))
    file_size: Mapped[int] = mapped_column(BigInteger)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[ImagingStudyStatus] = mapped_column(
        Enum(
            ImagingStudyStatus,
            name="imaging_study_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
