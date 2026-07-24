import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

bearer = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DatabaseSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials)
        user = db.get(User, uuid.UUID(payload["sub"]))
        if user is None or not user.is_active or user.token_version != payload.get("ver"):
            raise unauthorized
        return user
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise unauthorized from exc


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
