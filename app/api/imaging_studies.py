import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.imaging_study import ImagingStudyRead
from app.services.audit_service import AuditService
from app.services.imaging_study_service import (
    ImagingStudyNotFoundError,
    ImagingStudyService,
    PatientNotFoundError,
    InvalidDicomFileError,
)
from app.storage.file_storage import (
    EmptyFileError,
    FileTooLargeError,
    LocalFileStorage,
    get_file_storage,
)

router = APIRouter(tags=["imaging-studies"])
Storage = Annotated[LocalFileStorage, Depends(get_file_storage)]


def service(db: DatabaseSession, storage: Storage) -> ImagingStudyService:
    return ImagingStudyService(db, storage)


@router.post(
    "/patients/{patient_id}/imaging-studies",
    response_model=ImagingStudyRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_imaging_study(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    imaging_service: Annotated[ImagingStudyService, Depends(service)],
    file: Annotated[UploadFile, File()],
):
    try:
        study = imaging_service.create(
            patient_id=patient_id,
            original_filename=file.filename or "",
            source=file.file,
        )
        AuditService(db).record(
            "DICOM_UPLOADED",
            "imaging_study",
            study.id,
            current_user.id,
            {"patient_id": str(patient_id), "sha256": study.sha256},
        )
        return study
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc
    except InvalidDicomFileError as exc:
        raise HTTPException(
            status_code=415, detail="A valid DICOM .dcm file is required"
        ) from exc
    except EmptyFileError as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is empty") from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Uploaded file is too large") from exc


@router.get(
    "/patients/{patient_id}/imaging-studies",
    response_model=list[ImagingStudyRead],
)
def list_imaging_studies(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    imaging_service: Annotated[ImagingStudyService, Depends(service)],
):
    try:
        return imaging_service.list_for_patient(patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc


@router.get("/imaging-studies/{study_id}", response_model=ImagingStudyRead)
def get_imaging_study(
    study_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    imaging_service: Annotated[ImagingStudyService, Depends(service)],
):
    try:
        study = imaging_service.get(study_id)
        AuditService(db).record(
            "DICOM_VIEWED", "imaging_study", study.id, current_user.id
        )
        return study
    except ImagingStudyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Imaging study not found") from exc


@router.delete("/imaging-studies/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imaging_study(
    study_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    imaging_service: Annotated[ImagingStudyService, Depends(service)],
) -> None:
    try:
        imaging_service.delete(study_id)
        AuditService(db).record(
            "DICOM_DELETED", "imaging_study", study_id, current_user.id
        )
    except ImagingStudyNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Imaging study not found") from exc
