from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AdminUser, DatabaseSession
from app.schemas.audit import AuditEventRead
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-events", tags=["audit"])


def service(db: DatabaseSession) -> AuditService:
    return AuditService(db)


@router.get("", response_model=list[AuditEventRead])
def list_audit_events(
    _: AdminUser,
    audit_service: Annotated[AuditService, Depends(service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return audit_service.list(limit=limit, offset=offset)
