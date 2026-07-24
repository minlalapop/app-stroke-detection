import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUser, DatabaseSession
from app.models.export import ExportFormat
from app.schemas.export import ReportExportRead
from app.services.audit_service import AuditService
from app.services.export_service import (
    ExportNotFoundError,
    ExportService,
    ReportNotFoundError,
    ReportNotReadyForExportError,
)
from app.storage.file_storage import LocalFileStorage, get_file_storage

router = APIRouter(tags=["exports"])
Storage = Annotated[LocalFileStorage, Depends(get_file_storage)]


def service(db: DatabaseSession, storage: Storage) -> ExportService:
    return ExportService(db, storage)


@router.post(
    "/reports/{report_id}/exports/{export_format}",
    response_model=ReportExportRead,
    status_code=status.HTTP_201_CREATED,
)
def create_export(
    report_id: uuid.UUID,
    export_format: ExportFormat,
    current_user: CurrentUser,
    db: DatabaseSession,
    export_service: Annotated[ExportService, Depends(service)],
):
    try:
        export = export_service.create(report_id, export_format, current_user)
        AuditService(db).record(
            "REPORT_EXPORTED",
            "report_export",
            export.id,
            current_user.id,
            {"report_id": str(report_id), "format": export.format.value},
        )
        return export
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc
    except ReportNotReadyForExportError as exc:
        raise HTTPException(
            status_code=409, detail="Report is not ready for export"
        ) from exc


@router.get("/reports/{report_id}/exports", response_model=list[ReportExportRead])
def list_exports(
    report_id: uuid.UUID,
    _: CurrentUser,
    export_service: Annotated[ExportService, Depends(service)],
):
    try:
        return export_service.list_for_report(report_id)
    except ReportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Report not found") from exc


@router.get("/exports/{export_id}/download")
def download_export(
    export_id: uuid.UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    storage: Storage,
    export_service: Annotated[ExportService, Depends(service)],
):
    try:
        export = export_service.get(export_id)
    except ExportNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Export not found") from exc
    media_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    AuditService(db).record(
        "EXPORT_DOWNLOADED",
        "report_export",
        export.id,
        current_user.id,
        {"format": export.format.value},
    )
    return FileResponse(
        storage.path_for_uri(export.file_uri),
        media_type=media_types[export.format],
        filename=f"report-{export.report_id}.{export.format.value}",
    )
