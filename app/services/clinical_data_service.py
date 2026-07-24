import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinical_data import ClinicalData
from app.models.patient import Patient
from app.schemas.clinical_data import ClinicalDataCreate


class PatientNotFoundError(Exception):
    pass


class ClinicalDataNotFoundError(Exception):
    pass


class ClinicalDataService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, patient_id: uuid.UUID, data: ClinicalDataCreate) -> ClinicalData:
        if self.db.get(Patient, patient_id) is None:
            raise PatientNotFoundError
        clinical_data = ClinicalData(patient_id=patient_id, **data.model_dump())
        self.db.add(clinical_data)
        self.db.commit()
        self.db.refresh(clinical_data)
        return clinical_data

    def list_for_patient(self, patient_id: uuid.UUID) -> list[ClinicalData]:
        if self.db.get(Patient, patient_id) is None:
            raise PatientNotFoundError
        statement = (
            select(ClinicalData)
            .where(ClinicalData.patient_id == patient_id)
            .order_by(ClinicalData.created_at, ClinicalData.id)
        )
        return list(self.db.scalars(statement).all())

    def get_for_patient(
        self, patient_id: uuid.UUID, clinical_data_id: uuid.UUID
    ) -> ClinicalData:
        clinical_data = self.db.scalar(
            select(ClinicalData).where(
                ClinicalData.id == clinical_data_id,
                ClinicalData.patient_id == patient_id,
            )
        )
        if clinical_data is None:
            raise ClinicalDataNotFoundError
        return clinical_data

    def update(
        self,
        patient_id: uuid.UUID,
        clinical_data_id: uuid.UUID,
        data: ClinicalDataCreate,
    ) -> ClinicalData:
        clinical_data = self.get_for_patient(patient_id, clinical_data_id)
        for field, value in data.model_dump().items():
            setattr(clinical_data, field, value)
        self.db.commit()
        self.db.refresh(clinical_data)
        return clinical_data
