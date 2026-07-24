from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.core.security import create_access_token
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserRead
from app.services.audit_service import AuditService
from app.services.user_service import InvalidCredentialsError, UsernameAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["authentication"])


def service(db: DatabaseSession) -> UserService:
    return UserService(db)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(service)],
):
    try:
        user = user_service.authenticate(payload.login_email(), payload.password)
    except InvalidCredentialsError as exc:
        detail_key = "email" if payload.email is not None else "username"
        AuditService(db).record(
            "LOGIN_FAILED",
            "authentication",
            details={detail_key: payload.login_email()},
        )
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc
    AuditService(db).record("LOGIN_SUCCEEDED", "user", user.id, user.id)
    return TokenResponse(access_token=create_access_token(str(user.id), user.token_version))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    db: DatabaseSession,
    user_service: Annotated[UserService, Depends(service)],
):
    user_service.ensure_default_admin()
    try:
        user = user_service.create_doctor(payload)
        AuditService(db).record("USER_REGISTERED", "user", user.id, user.id)
        return user
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail="Un compte existe déjà avec cet email.",
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: CurrentUser, db: DatabaseSession) -> None:
    UserService(db).logout(current_user)
    AuditService(db).record("LOGOUT", "user", current_user.id, current_user.id)


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser):
    return current_user
