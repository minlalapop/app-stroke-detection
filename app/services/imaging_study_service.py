import uuid
from pathlib import Path
from typing import BinaryIO

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.imaging_study import ImagingStudy, ImagingStudyStatus
from app.models.patient import Patient
from app.storage.file_storage import LocalFileStorage


class PatientNotFoundError(Exception):
    pass


class ImagingStudyNotFoundError(Exception):
    pass


class InvalidDicomFileError(Exception):
    pass


def validate_dicom(filename: str, source: BinaryIO) -> dict[str, str]:
    normalized = Path(filename).name.lower()
    if not normalized.endswith(".dcm") or len(Path(filename).name) > 255:
        raise InvalidDicomFileError
    try:
        dataset = dcmread(source, defer_size="1 KB", force=False)
        if "PixelData" not in dataset:
            raise InvalidDicomFileError
    except (InvalidDicomError, EOFError, OSError, ValueError) as exc:
        raise InvalidDicomFileError from exc
    finally:
        source.seek(0)
    metadata = {}
    for keyword in (
        "StudyInstanceUID",
        "SeriesInstanceUID",
        "SOPInstanceUID",
        "Modality",
        "StudyDate",
    ):
        value = getattr(dataset, keyword, None)
        if value not in (None, ""):
            metadata[keyword] = str(value)
    return metadata


class ImagingStudyService:
    def __init__(self, db: Session, storage: LocalFileStorage) -> None:
        self.db = db
        self.storage = storage

    def create(
        self,
        patient_id: uuid.UUID,
        original_filename: str,
        source: BinaryIO,
    ) -> ImagingStudy:
        if self.db.get(Patient, patient_id) is None:
            raise PatientNotFoundError
        metadata = validate_dicom(original_filename, source)
        study_id = uuid.uuid4()
        stored = self.storage.save_study(study_id, source, ".dcm")
        study = ImagingStudy(
            id=study_id,
            patient_id=patient_id,
            modality=metadata.get("Modality", "UNKNOWN"),
            original_filename=Path(original_filename).name,
            original_file_uri=stored.uri,
            sha256=stored.sha256,
            file_size=stored.size,
            metadata_json=metadata,
            status=ImagingStudyStatus.UPLOADED,
        )
        try:
            self.db.add(study)
            self.db.commit()
            self.db.refresh(study)
        except Exception:
            self.db.rollback()
            self.storage.delete(stored.uri)
            raise
        return study

    def list_for_patient(self, patient_id: uuid.UUID) -> list[ImagingStudy]:
        if self.db.get(Patient, patient_id) is None:
            raise PatientNotFoundError
        statement = (
            select(ImagingStudy)
            .where(ImagingStudy.patient_id == patient_id)
            .order_by(ImagingStudy.created_at, ImagingStudy.id)
        )
        return list(self.db.scalars(statement).all())

    def get(self, study_id: uuid.UUID) -> ImagingStudy:
        study = self.db.get(ImagingStudy, study_id)
        if study is None:
            raise ImagingStudyNotFoundError
        return study

    def delete(self, study_id: uuid.UUID) -> None:
        study = self.get(study_id)
        uri = study.original_file_uri
        self.db.delete(study)
        self.db.commit()
        self.storage.delete(uri)
