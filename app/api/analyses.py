import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.api.model_services import get_image_model_service, get_tabular_model_service
from app.schemas.analysis import AnalysisCreate, AnalysisRead
from app.services.audit_service import AuditService
from app.services.analysis_service import (
    AnalysisAlreadyRunError,
    AnalysisDetails,
    AnalysisInputError,
    AnalysisNotFoundError,
    AnalysisService,
)
from app.services.image_model_service import ImageModelService
from app.services.tabular_model_service import TabularModelService

router = APIRouter(tags=["analyses"])


def service(
    db: DatabaseSession,
    tabular: Annotated[TabularModelService, Depends(get_tabular_model_service)],
    image: Annotated[ImageModelService, Depends(get_image_model_service)],
) -> AnalysisService:
    return AnalysisService(db, tabular, image)


def response(details: AnalysisDetails) -> AnalysisRead:
    analysis = details.analysis
    return AnalysisRead(
        id=analysis.id,
        patient_id=analysis.patient_id,
        clinical_data_id=analysis.clinical_data_id,
        imaging_study_id=analysis.imaging_study_id,
        status=analysis.status,
        created_by_user_id=analysis.created_by_user_id,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        tabular_result=details.tabular_result,
        imaging_result=details.imaging_result,
    )


@router.post("/analyses", response_model=AnalysisRead, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
    analysis_service: Annotated[AnalysisService, Depends(service)],
):
    try:
        analysis = analysis_service.create(payload, current_user)
        AuditService(db).record(
            "ANALYSIS_CREATED", "analysis", analysis.id, current_user.id,
            {"patient_id": str(analysis.patient_id)},
        )
        return response(analysis_service.get(analysis.id))
    except AnalysisInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analyses", response_model=list[AnalysisRead])
def list_analyses(
    current_user: CurrentUser,
    analysis_service: Annotated[AnalysisService, Depends(service)],
):
    return [response(item) for item in analysis_service.list_all()]


@router.get("/analyses/{analysis_id}", response_model=AnalysisRead)
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    analysis_service: Annotated[AnalysisService, Depends(service)],
):
    try:
        details = analysis_service.get(analysis_id)
        AuditService(db).record(
            "ANALYSIS_RESULT_VIEWED", "analysis", analysis_id, current_user.id
        )
        return response(details)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Analysis not found") from exc


@router.get("/patients/{patient_id}/analyses", response_model=list[AnalysisRead])
def list_patient_analyses(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    analysis_service: Annotated[AnalysisService, Depends(service)],
):
    try:
        return [response(item) for item in analysis_service.list_for_patient(patient_id)]
    except AnalysisInputError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/analyses/{analysis_id}/run", response_model=AnalysisRead)
def run_analysis(
    analysis_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    analysis_service: Annotated[AnalysisService, Depends(service)],
):
    try:
        details = analysis_service.run(analysis_id)
        AuditService(db).record(
            "ANALYSIS_RUN",
            "analysis",
            analysis_id,
            current_user.id,
            {
                "status": details.analysis.status.value,
                "tabular_model_version": details.tabular_result.model_version
                if details.tabular_result else None,
                "image_model_version": details.imaging_result.model_version
                if details.imaging_result else None,
            },
        )
        return response(details)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Analysis not found") from exc
    except AnalysisAlreadyRunError as exc:
        raise HTTPException(status_code=409, detail="Analysis has already been run") from exc
    except AnalysisInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
