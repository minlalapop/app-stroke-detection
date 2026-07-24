import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ValidationStatus(str, enum.Enum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class DoctorValidation(Base):
    __tablename__ = "doctor_validations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    validation_status: Mapped[ValidationStatus] = mapped_column(
        Enum(
            ValidationStatus,
            name="validation_status",
            values_callable=lambda values: [value.value for value in values],
        )
    )
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
