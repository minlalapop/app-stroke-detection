import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        action: str,
        entity_type: str,
        entity_id: str | uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        details: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details_json=details or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list(self, limit: int = 100, offset: int = 0) -> list[AuditEvent]:
        statement = (
            select(AuditEvent)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement).all())
