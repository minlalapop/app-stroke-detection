import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class PatientNotFoundError(Exception):
    pass


class PatientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: PatientCreate) -> Patient:
        patient = Patient(**data.model_dump())
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def list(self) -> list[Patient]:
        statement = select(Patient).order_by(Patient.created_at.desc(), Patient.id.desc())
        return list(self.db.scalars(statement).all())

    def get(self, patient_id: uuid.UUID) -> Patient:
        patient = self.db.get(Patient, patient_id)
        if patient is None:
            raise PatientNotFoundError
        return patient

    def update(self, patient_id: uuid.UUID, data: PatientUpdate) -> Patient:
        patient = self.get(patient_id)
        for field, value in data.model_dump().items():
            setattr(patient, field, value)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def delete(self, patient_id: uuid.UUID) -> None:
        patient = self.get(patient_id)
        self.db.delete(patient)
        self.db.commit()
