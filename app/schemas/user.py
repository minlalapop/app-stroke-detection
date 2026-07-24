import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    username: str | None = Field(default=None, exclude=True)
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def require_email(self):
        if self.email is None and self.username is None:
            raise ValueError("email is required")
        if self.email is not None and ("@" not in self.email or self.email.startswith("@")):
            raise ValueError("invalid email address")
        return self

    @field_validator("email", "username")
    @classmethod
    def normalize_login(cls, value: str | None) -> str | None:
        return value.strip().lower() if value is not None else None

    def login_email(self) -> str:
        return self.email or self.username or ""

    @field_validator("full_name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class UserAdminCreate(UserCreate):
    role: UserRole = UserRole.DOCTOR
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    email: str | None = None
    username: str | None = None
    password: str

    @model_validator(mode="after")
    def require_login(self):
        if self.email is None and self.username is None:
            raise ValueError("email is required")
        return self

    def login_email(self) -> str:
        return (self.email or self.username or "").strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
