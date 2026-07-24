import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ClinicalData(Base):
    __tablename__ = "clinical_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    age: Mapped[float | None] = mapped_column(Float, nullable=True)
    hypertension: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    heart_disease: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ever_married: Mapped[str | None] = mapped_column(String(3), nullable=True)
    work_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    residence_type: Mapped[str | None] = mapped_column(String(5), nullable=True)
    avg_glucose_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    smoking_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
