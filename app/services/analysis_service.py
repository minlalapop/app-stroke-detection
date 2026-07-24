import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis, AnalysisStatus
from app.models.clinical_data import ClinicalData
from app.models.imaging_study import ImagingStudy
from app.models.patient import Patient
from app.models.prediction import (
    ImageSegmentationResult,
    ModelResultStatus,
    TabularPrediction,
)
from app.models.user import User
from app.schemas.analysis import AnalysisCreate
from app.services.image_model_service import ImageModelService
from app.services.model_common import ModelExecutionStatus
from app.services.tabular_model_service import TabularModelService


class AnalysisNotFoundError(Exception):
    pass


class AnalysisInputError(Exception):
    pass


class AnalysisAlreadyRunError(Exception):
    pass


@dataclass
class AnalysisDetails:
    analysis: Analysis
    tabular_result: TabularPrediction | None
    imaging_result: ImageSegmentationResult | None


class AnalysisService:
    def __init__(
        self,
        db: Session,
        tabular_model: TabularModelService,
        image_model: ImageModelService,
    ) -> None:
        self.db = db
        self.tabular_model = tabular_model
        self.image_model = image_model

    def create(self, data: AnalysisCreate, created_by: User) -> Analysis:
        if self.db.get(Patient, data.patient_id) is None:
            raise AnalysisInputError("Patient not found")
        if data.clinical_data_id is not None:
            clinical = self.db.get(ClinicalData, data.clinical_data_id)
            if clinical is None or clinical.patient_id != data.patient_id:
                raise AnalysisInputError("Clinical data does not belong to patient")
        if data.imaging_study_id is not None:
            study = self.db.get(ImagingStudy, data.imaging_study_id)
            if study is None or study.patient_id != data.patient_id:
                raise AnalysisInputError("Imaging study does not belong to patient")
        analysis = Analysis(
            **data.model_dump(),
            status=AnalysisStatus.READY,
            created_by_user_id=created_by.id,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get(self, analysis_id: uuid.UUID) -> AnalysisDetails:
        analysis = self.db.get(Analysis, analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError
        return AnalysisDetails(
            analysis=analysis,
            tabular_result=self.db.scalar(
                select(TabularPrediction).where(TabularPrediction.analysis_id == analysis_id)
            ),
            imaging_result=self.db.scalar(
                select(ImageSegmentationResult).where(
                    ImageSegmentationResult.analysis_id == analysis_id
                )
            ),
        )

    def list_for_patient(self, patient_id: uuid.UUID) -> list[AnalysisDetails]:
        if self.db.get(Patient, patient_id) is None:
            raise AnalysisInputError("Patient not found")
        analyses = self.db.scalars(
            select(Analysis)
            .where(Analysis.patient_id == patient_id)
            .order_by(Analysis.created_at, Analysis.id)
        ).all()
        return [self.get(analysis.id) for analysis in analyses]

    def list_all(self) -> list[AnalysisDetails]:
        analyses = self.db.scalars(
            select(Analysis).order_by(Analysis.created_at.desc(), Analysis.id.desc())
        ).all()
        return [self.get(analysis.id) for analysis in analyses]

    def run(self, analysis_id: uuid.UUID) -> AnalysisDetails:
        details = self.get(analysis_id)
        analysis = details.analysis
        if analysis.status != AnalysisStatus.READY:
            raise AnalysisAlreadyRunError
        analysis.status = AnalysisStatus.PROCESSING
        self.db.commit()

        result_statuses: list[ModelResultStatus] = []
        if analysis.clinical_data_id is not None:
            clinical = self.db.get(ClinicalData, analysis.clinical_data_id)
            patient = self.db.get(Patient, analysis.patient_id)
            if clinical is None:
                raise AnalysisInputError("Clinical data is no longer available")
            if patient is None:
                raise AnalysisInputError("Patient is no longer available")
            model_result = self.tabular_model.predict(
                {
                    "gender": patient.sex,
                    "age": clinical.age,
                    "hypertension": None
                    if clinical.hypertension is None
                    else int(clinical.hypertension),
                    "heart_disease": None
                    if clinical.heart_disease is None
                    else int(clinical.heart_disease),
                    "ever_married": clinical.ever_married,
                    "work_type": clinical.work_type,
                    "Residence_type": clinical.residence_type,
                    "avg_glucose_level": clinical.avg_glucose_level,
                    "bmi": clinical.bmi,
                    "smoking_status": clinical.smoking_status,
                }
            )
            result_status = self._result_status(model_result["status"])
            result_statuses.append(result_status)
            self.db.add(
                TabularPrediction(
                    analysis_id=analysis.id,
                    status=result_status,
                    risk_score=model_result.get("risk_score"),
                    risk_label=model_result.get("risk_label"),
                    model_version=model_result.get("model_version"),
                    error_message=model_result.get("error_message"),
                )
            )

        if analysis.imaging_study_id is not None:
            model_result = self.image_model.segment(str(analysis.imaging_study_id))
            result_status = self._result_status(model_result["status"])
            result_statuses.append(result_status)
            self.db.add(
                ImageSegmentationResult(
                    analysis_id=analysis.id,
                    status=result_status,
                    lesion_detected=model_result.get("lesion_detected"),
                    lesion_volume_ml=model_result.get("lesion_volume_ml"),
                    mask_uri=model_result.get("mask_uri"),
                    preview_uri=model_result.get("preview_uri"),
                    model_version=model_result.get("model_version"),
                    error_message=model_result.get("error_message"),
                )
            )

        analysis.status = self._analysis_status(result_statuses)
        self.db.commit()
        return self.get(analysis.id)

    @staticmethod
    def _result_status(status: ModelExecutionStatus | str) -> ModelResultStatus:
        value = status.value if isinstance(status, ModelExecutionStatus) else status
        return ModelResultStatus(value)

    @staticmethod
    def _analysis_status(statuses: list[ModelResultStatus]) -> AnalysisStatus:
        if statuses and all(status == ModelResultStatus.COMPLETED for status in statuses):
            return AnalysisStatus.COMPLETED
        if any(status == ModelResultStatus.COMPLETED for status in statuses):
            return AnalysisStatus.PARTIAL_COMPLETED
        if statuses and all(
            status == ModelResultStatus.MODEL_NOT_AVAILABLE for status in statuses
        ):
            return AnalysisStatus.MODEL_NOT_AVAILABLE
        return AnalysisStatus.FAILED
