from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AVC Medical Analysis API"
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/med_stroke"
    )
    jwt_secret_key: str = "change-this-secret-before-deployment"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    file_storage_root: str = "storage"
    max_upload_size_mb: int = 512
    tabular_model_path: str | None = None
    image_model_path: str | None = None
    llm_model_path: str | None = None
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
