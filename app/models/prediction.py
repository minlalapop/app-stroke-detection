import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelResultStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    FAILED = "FAILED"


class TabularPrediction(Base):
    __tablename__ = "tabular_predictions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    status: Mapped[ModelResultStatus] = mapped_column(
        Enum(
            ModelResultStatus,
            name="model_result_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ImageSegmentationResult(Base):
    __tablename__ = "image_segmentation_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    status: Mapped[ModelResultStatus] = mapped_column(
        Enum(
            ModelResultStatus,
            name="model_result_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    lesion_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    lesion_volume_ml: Mapped[float | None] = mapped_column(Float, nullable=True)
    mask_uri: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    preview_uri: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
