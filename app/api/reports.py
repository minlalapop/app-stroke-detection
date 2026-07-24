import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.core.config import get_settings
from app.schemas.report import ReportRead
from app.services.audit_service import AuditService
from app.services.llm_enrichment_service import LLMEnrichmentService
from app.services.report_service import (
    AnalysisNotFoundError,
    DoctorRequiredError,
    LLMDraftNotReadyError,
    ReportAlreadyExistsError,
    ReportNotFoundError,
    ReportService,
    ReportValidationRequiredError,
)
from app.storage.file_storage import LocalFileStorage, get_file_storage

router = APIRouter(tags=["reports"])
Storage = Annotated[LocalFileStorage, Depends(get_file_storage)]


def get_llm_enrichment_service() -> LLMEnrichmentService:
    return LLMEnrichmentService(model_path=get_settings().llm_model_path)


def service(
    db: DatabaseSession,
    storage: Storage,
    llm: Annotated[LLMEnrichmentService, Depends(get_llm_enrichment_service)],
) -> ReportService:
    return ReportService(db, storage, llm)


@router.post(
    "/analyses/{analysis_id}/report",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
)
def generate_report(
    analysis_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    report_service: Annotated[ReportService, Depends(service)],
):
    try:
        report = report_service.generate(analysis_id, current_user)
        AuditService(db).record(
            "REPORT_GENERATED",
            "report",
            report.id,
            current_user.id,
            {"analysis_id": str(analysis_id), "llm_status": report.llm_status.value},
        )
        return report
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Analysis not found") from exc
    except ReportValidationRequiredError as exc:
        raise HTTPException(
            status_code=409,
            detail="Report cannot be generated before doctor validation.",
        ) from exc
    except ReportAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Report already exists") from exc


@router.get("/analyses/{analysis_id}/report", response_model=ReportRead)
def get_report(
    analysis_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    report_service: Annotated[ReportService, Depends(service)],
):
    try:
        report = report_service.get(analysis_id)
        AuditService(db).record("REPORT_VIEWED", "report", report.id, current_user.id)
        return report
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc


@router.post("/reports/{report_id}/approve-llm", response_model=ReportRead)
def approve_llm_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    report_service: Annotated[ReportService, Depends(service)],
):
    try:
        report = report_service.approve_llm_draft(report_id, current_user)
        AuditService(db).record(
            "LLM_DRAFT_APPROVED", "report", report.id, current_user.id
        )
        return report
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc
    except DoctorRequiredError as exc:
        raise HTTPException(status_code=403, detail="A doctor account is required") from exc
    except LLMDraftNotReadyError as exc:
        raise HTTPException(
            status_code=409, detail="No LLM draft is waiting for medical review"
        ) from exc
