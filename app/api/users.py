import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AdminUser, DatabaseSession
from app.schemas.user import UserAdminCreate, UserRead, UserUpdate
from app.services.audit_service import AuditService
from app.services.user_service import UserNotFoundError, UsernameAlreadyExistsError, UserService

router = APIRouter(prefix="/users", tags=["users"])


def service(db: DatabaseSession) -> UserService:
    return UserService(db)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserAdminCreate,
    admin: AdminUser,
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(service)],
):
    try:
        user = user_service.create(payload)
        AuditService(db).record("USER_CREATED", "user", user.id, admin.id)
        return user
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail="Username already exists") from exc


@router.get("", response_model=list[UserRead])
def list_users(_: AdminUser, user_service: Annotated[UserService, Depends(service)]):
    return user_service.list()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID,
    admin: AdminUser,
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(service)],
):
    try:
        return user_service.get(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    admin: AdminUser,
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(service)],
):
    try:
        user = user_service.update(user_id, payload)
        AuditService(db).record(
            "USER_UPDATED",
            "user",
            user.id,
            admin.id,
            {"changed_fields": sorted(payload.model_dump(exclude_unset=True))},
        )
        return user
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
