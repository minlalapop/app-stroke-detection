import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.clinical_data import ClinicalDataCreate, ClinicalDataRead
from app.services.audit_service import AuditService
from app.services.clinical_data_service import (
    ClinicalDataNotFoundError,
    ClinicalDataService,
    PatientNotFoundError,
)

router = APIRouter(prefix="/patients/{patient_id}/clinical-data", tags=["clinical-data"])


def service(db: DatabaseSession) -> ClinicalDataService:
    return ClinicalDataService(db)


@router.post("", response_model=ClinicalDataRead, status_code=status.HTTP_201_CREATED)
def create_clinical_data(
    patient_id: uuid.UUID,
    payload: ClinicalDataCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
    clinical_service: Annotated[ClinicalDataService, Depends(service)],
):
    try:
        clinical = clinical_service.create(patient_id, payload)
        AuditService(db).record(
            "CLINICAL_DATA_CREATED", "clinical_data", clinical.id, current_user.id,
            {"patient_id": str(patient_id)},
        )
        return clinical
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc


@router.get("", response_model=list[ClinicalDataRead])
def list_clinical_data(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    clinical_service: Annotated[ClinicalDataService, Depends(service)],
):
    try:
        return clinical_service.list_for_patient(patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc


@router.get("/{clinical_data_id}", response_model=ClinicalDataRead)
def get_clinical_data(
    patient_id: uuid.UUID,
    clinical_data_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    clinical_service: Annotated[ClinicalDataService, Depends(service)],
):
    try:
        clinical = clinical_service.get_for_patient(patient_id, clinical_data_id)
        AuditService(db).record(
            "CLINICAL_DATA_VIEWED", "clinical_data", clinical.id, current_user.id
        )
        return clinical
    except ClinicalDataNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Clinical data not found") from exc


@router.put("/{clinical_data_id}", response_model=ClinicalDataRead)
def update_clinical_data(
    patient_id: uuid.UUID,
    clinical_data_id: uuid.UUID,
    payload: ClinicalDataCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
    clinical_service: Annotated[ClinicalDataService, Depends(service)],
):
    try:
        clinical = clinical_service.update(patient_id, clinical_data_id, payload)
        AuditService(db).record(
            "CLINICAL_DATA_UPDATED", "clinical_data", clinical.id, current_user.id
        )
        return clinical
    except ClinicalDataNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Clinical data not found") from exc
