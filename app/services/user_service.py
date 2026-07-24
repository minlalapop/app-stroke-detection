import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserAdminCreate, UserCreate, UserUpdate


class UserNotFoundError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_default_admin(self) -> User:
        settings = get_settings()
        existing = self.get_by_username(settings.default_admin_username)
        if existing is not None:
            return existing
        admin = User(
            username=settings.default_admin_username.lower(),
            email=f"{settings.default_admin_username.lower()}@neuroflow.local",
            full_name="Administrator",
            password_hash=hash_password(settings.default_admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin

    def get_by_username(self, username: str) -> User | None:
        login = username.strip().lower()
        return self.db.scalar(
            select(User).where((User.email == login) | (User.username == login))
        )

    def authenticate(self, username: str, password: str) -> User:
        self.ensure_default_admin()
        user = self.get_by_username(username)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        return user

    def create_doctor(self, data: UserCreate) -> User:
        email = data.email or f"{data.username}@legacy.local"
        payload = UserAdminCreate(
            email=email,
            username=data.username,
            full_name=data.full_name,
            password=data.password,
            role=UserRole.DOCTOR,
        )
        return self.create(payload)

    def create(self, data: UserAdminCreate) -> User:
        email = data.login_email()
        if self.get_by_username(email) is not None:
            raise UsernameAlreadyExistsError
        user = User(
            username=data.username or email,
            email=email,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.username)).all())

    def get(self, user_id: uuid.UUID) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise UserNotFoundError
        return user

    def update(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = self.get(user_id)
        values = data.model_dump(exclude_unset=True)
        password = values.pop("password", None)
        for field, value in values.items():
            setattr(user, field, value)
        if password is not None:
            user.password_hash = hash_password(password)
            user.token_version += 1
        self.db.commit()
        self.db.refresh(user)
        return user

    def logout(self, user: User) -> None:
        user.token_version += 1
        self.db.commit()
