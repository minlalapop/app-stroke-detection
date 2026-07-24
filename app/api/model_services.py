from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUser
from app.core.config import get_settings
from app.services.image_model_service import ImageModelService
from app.services.tabular_model_service import TabularModelService

router = APIRouter(prefix="/models", tags=["models"])


def get_tabular_model_service() -> TabularModelService:
    return TabularModelService(model_path=get_settings().tabular_model_path)


def get_image_model_service() -> ImageModelService:
    return ImageModelService(model_path=get_settings().image_model_path)


@router.get("/status")
def model_status(
    _: CurrentUser,
    tabular: Annotated[TabularModelService, Depends(get_tabular_model_service)],
    image: Annotated[ImageModelService, Depends(get_image_model_service)],
) -> dict:
    return {
        "tabular_model": {
            "available": tabular.is_available(),
            "status": tabular.status(),
        },
        "image_model": {
            "available": image.is_available(),
            "status": image.status(),
        },
    }
