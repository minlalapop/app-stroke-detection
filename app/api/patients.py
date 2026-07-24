import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.audit_service import AuditService
from app.services.patient_service import PatientNotFoundError, PatientService

router = APIRouter(prefix="/patients", tags=["patients"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def service(db: DatabaseSession) -> PatientService:
    return PatientService(db)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
    patient_service: Annotated[PatientService, Depends(service)],
):
    patient = patient_service.create(payload)
    AuditService(db).record("PATIENT_CREATED", "patient", patient.id, current_user.id)
    return patient


@router.get("", response_model=list[PatientRead])
def list_patients(
    current_user: CurrentUser,
    db: DatabaseSession,
    patient_service: Annotated[PatientService, Depends(service)],
):
    return patient_service.list()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    patient_service: Annotated[PatientService, Depends(service)],
):
    try:
        patient = patient_service.get(patient_id)
        AuditService(db).record("PATIENT_VIEWED", "patient", patient.id, current_user.id)
        return patient
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc


@router.put("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
    patient_service: Annotated[PatientService, Depends(service)],
):
    try:
        patient = patient_service.update(patient_id, payload)
        AuditService(db).record("PATIENT_UPDATED", "patient", patient.id, current_user.id)
        return patient
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    patient_service: Annotated[PatientService, Depends(service)],
) -> None:
    try:
        patient_service.get(patient_id)
        AuditService(db).record(
            "PATIENT_DELETED", "patient", patient_id, current_user.id
        )
        patient_service.delete(patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc
