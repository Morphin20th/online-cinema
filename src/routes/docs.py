from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from src.dependencies import admin_required
from src.config import get_settings

router = APIRouter()

settings = get_settings()


@router.get(
    settings.DOCS_URL, include_in_schema=False, dependencies=[Depends(admin_required)]
)
def custom_swagger_ui():
    """Serve custom Swagger UI for admin users."""
    return get_swagger_ui_html(openapi_url="/openapi.json/", title="Docs")


@router.get(
    settings.REDOC_URL, include_in_schema=False, dependencies=[Depends(admin_required)]
)
def custom_redoc_html():
    """Serve custom ReDoc UI for admin users."""
    return get_redoc_html(openapi_url="/openapi.json/", title="Redoc")


@router.get(
    settings.OPENAPI_URL,
    include_in_schema=False,
    dependencies=[Depends(admin_required)],
)
def custom_openapi() -> Dict[str, Any]:
    """Serve custom OpenAPI schema for admin users."""
    from src.main import app

    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
