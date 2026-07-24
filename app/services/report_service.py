import json
import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis, AnalysisStatus
from app.models.clinical_data import ClinicalData
from app.models.patient import Patient
from app.models.prediction import ImageSegmentationResult, ModelResultStatus, TabularPrediction
from app.models.report import Report, ReportStatus
from app.models.user import User, UserRole
from app.models.validation import DoctorValidation, ValidationStatus
from app.services.llm_enrichment_service import LLMEnrichmentService
from app.services.model_common import ModelExecutionStatus
from app.storage.file_storage import LocalFileStorage


class AnalysisNotFoundError(Exception):
    pass


class ReportValidationRequiredError(Exception):
    pass


class ReportAlreadyExistsError(Exception):
    pass


class ReportNotFoundError(Exception):
    pass


class LLMDraftNotReadyError(Exception):
    pass


class DoctorRequiredError(Exception):
    pass


class ReportService:
    def __init__(
        self,
        db: Session,
        storage: LocalFileStorage,
        llm: LLMEnrichmentService,
    ) -> None:
        self.db = db
        self.storage = storage
        self.llm = llm

    def generate(self, analysis_id: uuid.UUID, generated_by: User) -> Report:
        analysis = self.db.get(Analysis, analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError
        validation = self.db.scalar(
            select(DoctorValidation).where(DoctorValidation.analysis_id == analysis_id)
        )
        if validation is None or validation.validation_status != ValidationStatus.VALIDATED:
            raise ReportValidationRequiredError
        if self.get_optional(analysis_id) is not None:
            raise ReportAlreadyExistsError

        report_id = uuid.uuid4()
        generated_at = datetime.now(timezone.utc)
        report_data = self._deterministic_data(analysis, validation, generated_at)
        deterministic_content = json.dumps(
            report_data,
            ensure_ascii=False,
            indent=2,
            default=self._json_default,
            sort_keys=True,
        ).encode("utf-8")
        deterministic_file = self.storage.save_report(
            report_id, deterministic_content, ".json"
        )

        llm_result = self.llm.enrich(report_data)
        llm_status = self._llm_status(llm_result["status"])
        llm_uri = None
        report_status = ReportStatus.READY_FOR_EXPORT
        if llm_status == ModelResultStatus.COMPLETED:
            draft = (
                "BROUILLON ENRICHI PAR LLM — VALIDATION MÉDICALE REQUISE AVANT EXPORT\n\n"
                + llm_result["enriched_text"]
            ).encode("utf-8")
            llm_file = self.storage.save_report(report_id, draft, ".llm-draft.txt")
            llm_uri = llm_file.uri
            report_status = ReportStatus.LLM_DRAFT_REVIEW_REQUIRED

        report = Report(
            id=report_id,
            analysis_id=analysis_id,
            deterministic_report_uri=deterministic_file.uri,
            deterministic_sha256=deterministic_file.sha256,
            llm_status=llm_status,
            llm_enriched_report_uri=llm_uri,
            status=report_status,
            generated_by=generated_by.id,
            generated_at=generated_at,
        )
        self.db.add(report)
        analysis.status = AnalysisStatus.REPORT_GENERATED
        try:
            self.db.commit()
            self.db.refresh(report)
        except Exception:
            self.db.rollback()
            self.storage.delete(deterministic_file.uri)
            if llm_uri:
                self.storage.delete(llm_uri)
            raise
        return report

    def approve_llm_draft(self, report_id: uuid.UUID, doctor: User) -> Report:
        if doctor.role != UserRole.DOCTOR:
            raise DoctorRequiredError
        report = self.db.get(Report, report_id)
        if report is None:
            raise ReportNotFoundError
        if report.status != ReportStatus.LLM_DRAFT_REVIEW_REQUIRED:
            raise LLMDraftNotReadyError
        report.status = ReportStatus.READY_FOR_EXPORT
        report.llm_approved_by = doctor.id
        report.llm_approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_optional(self, analysis_id: uuid.UUID) -> Report | None:
        return self.db.scalar(select(Report).where(Report.analysis_id == analysis_id))

    def get(self, analysis_id: uuid.UUID) -> Report:
        report = self.get_optional(analysis_id)
        if report is None:
            raise ReportNotFoundError
        return report

    def _deterministic_data(
        self,
        analysis: Analysis,
        validation: DoctorValidation,
        generated_at: datetime,
    ) -> dict:
        patient = self.db.get(Patient, analysis.patient_id)
        clinical = (
            self.db.get(ClinicalData, analysis.clinical_data_id)
            if analysis.clinical_data_id
            else None
        )
        tabular = self.db.scalar(
            select(TabularPrediction).where(TabularPrediction.analysis_id == analysis.id)
        )
        imaging = self.db.scalar(
            select(ImageSegmentationResult).where(
                ImageSegmentationResult.analysis_id == analysis.id
            )
        )
        doctor = self.db.get(User, validation.doctor_id)
        return {
            "report_type": "deterministic_medical_assistance_report",
            "analysis_id": analysis.id,
            "generated_at": generated_at,
            "patient": {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "birth_date": patient.birth_date,
                "sex": patient.sex,
            },
            "clinical_data": None
            if clinical is None
            else {
                "age": clinical.age,
                "hypertension": clinical.hypertension,
                "heart_disease": clinical.heart_disease,
                "ever_married": clinical.ever_married,
                "work_type": clinical.work_type,
                "residence_type": clinical.residence_type,
                "avg_glucose_level": clinical.avg_glucose_level,
                "bmi": clinical.bmi,
                "smoking_status": clinical.smoking_status,
            },
            "tabular_result": None
            if tabular is None
            else {
                "status": tabular.status,
                "risk_score": tabular.risk_score,
                "risk_label": tabular.risk_label,
                "model_version": tabular.model_version,
            },
            "imaging_result": None
            if imaging is None
            else {
                "status": imaging.status,
                "lesion_detected": imaging.lesion_detected,
                "lesion_volume_ml": imaging.lesion_volume_ml,
                "mask_uri": imaging.mask_uri,
                "model_version": imaging.model_version,
            },
            "doctor_validation": {
                "status": validation.validation_status,
                "comment": validation.comment,
                "validated_at": validation.validated_at,
                "doctor_id": validation.doctor_id,
                "doctor_name": doctor.full_name,
            },
            "limitations": [
                "Outil d’aide à la décision.",
                "Ne remplace pas l’avis médical.",
                "Les contenus enrichis par LLM sont des brouillons séparés nécessitant une validation médicale.",
            ],
        }

    @staticmethod
    def _llm_status(status: ModelExecutionStatus | str) -> ModelResultStatus:
        value = status.value if isinstance(status, ModelExecutionStatus) else status
        return ModelResultStatus(value)

    @staticmethod
    def _json_default(value):
        if isinstance(value, Enum):
            return value.value
        return str(value)
