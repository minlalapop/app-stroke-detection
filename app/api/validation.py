import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.validation import DoctorValidationCreate, DoctorValidationRead
from app.services.audit_service import AuditService
from app.services.validation_service import (
    AnalysisNotFoundError,
    AnalysisNotReadyForValidationError,
    DoctorRequiredError,
    ValidationAlreadyExistsError,
    ValidationNotFoundError,
    ValidationService,
)

router = APIRouter(tags=["validation"])


def service(db: DatabaseSession) -> ValidationService:
    return ValidationService(db)


@router.post(
    "/analyses/{analysis_id}/validate",
    response_model=DoctorValidationRead,
    status_code=status.HTTP_201_CREATED,
)
def validate_analysis(
    analysis_id: uuid.UUID,
    payload: DoctorValidationCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
    validation_service: Annotated[ValidationService, Depends(service)],
):
    try:
        validation = validation_service.create(analysis_id, current_user, payload)
        AuditService(db).record(
            "DOCTOR_VALIDATION_CREATED",
            "doctor_validation",
            validation.id,
            current_user.id,
            {
                "analysis_id": str(analysis_id),
                "status": validation.validation_status.value,
            },
        )
        return validation
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Analysis not found") from exc
    except DoctorRequiredError as exc:
        raise HTTPException(status_code=403, detail="A doctor account is required") from exc
    except AnalysisNotReadyForValidationError as exc:
        raise HTTPException(status_code=409, detail="Analysis is not ready for validation") from exc
    except ValidationAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Analysis has already been validated") from exc


@router.get("/analyses/{analysis_id}/validation", response_model=DoctorValidationRead)
def get_validation(
    analysis_id: uuid.UUID,
    _: CurrentUser,
    validation_service: Annotated[ValidationService, Depends(service)],
):
    try:
        return validation_service.get(analysis_id)
    except ValidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Validation not found") from exc
