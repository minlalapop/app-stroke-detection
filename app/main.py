from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyses import router as analyses_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.clinical_data import router as clinical_data_router
from app.api.exports import router as exports_router
from app.api.imaging_studies import router as imaging_studies_router
from app.api.model_services import router as model_services_router
from app.api.reports import router as reports_router
from app.api.patients import router as patients_router
from app.api.users import router as users_router
from app.api.validation import router as validation_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.frontend_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(auth_router)
    application.include_router(users_router)
    application.include_router(patients_router)
    application.include_router(clinical_data_router)
    application.include_router(imaging_studies_router)
    application.include_router(model_services_router)
    application.include_router(analyses_router)
    application.include_router(validation_router)
    application.include_router(reports_router)
    application.include_router(exports_router)
    application.include_router(audit_router)

    @application.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
