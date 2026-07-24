import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis, AnalysisStatus
from app.models.user import User, UserRole
from app.models.validation import DoctorValidation, ValidationStatus
from app.schemas.validation import DoctorValidationCreate


class AnalysisNotFoundError(Exception):
    pass


class ValidationNotFoundError(Exception):
    pass


class ValidationAlreadyExistsError(Exception):
    pass


class AnalysisNotReadyForValidationError(Exception):
    pass


class DoctorRequiredError(Exception):
    pass


class ValidationService:
    TERMINAL_STATUSES = {
        AnalysisStatus.COMPLETED,
        AnalysisStatus.PARTIAL_COMPLETED,
        AnalysisStatus.MODEL_NOT_AVAILABLE,
        AnalysisStatus.FAILED,
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        analysis_id: uuid.UUID,
        doctor: User,
        data: DoctorValidationCreate,
    ) -> DoctorValidation:
        if doctor.role != UserRole.DOCTOR:
            raise DoctorRequiredError
        analysis = self.db.get(Analysis, analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError
        if analysis.status not in self.TERMINAL_STATUSES:
            raise AnalysisNotReadyForValidationError
        if self.get_optional(analysis_id) is not None:
            raise ValidationAlreadyExistsError
        validation = DoctorValidation(
            analysis_id=analysis_id,
            doctor_id=doctor.id,
            **data.model_dump(),
        )
        self.db.add(validation)
        if data.validation_status == ValidationStatus.VALIDATED:
            analysis.status = AnalysisStatus.VALIDATED_BY_DOCTOR
        self.db.commit()
        self.db.refresh(validation)
        return validation

    def get_optional(self, analysis_id: uuid.UUID) -> DoctorValidation | None:
        return self.db.scalar(
            select(DoctorValidation).where(DoctorValidation.analysis_id == analysis_id)
        )

    def get(self, analysis_id: uuid.UUID) -> DoctorValidation:
        validation = self.get_optional(analysis_id)
        if validation is None:
            raise ValidationNotFoundError
        return validation
