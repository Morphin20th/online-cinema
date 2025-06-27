from typing import Dict, Any

from fastapi import APIRouter, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from src.dependencies import admin_required

router = APIRouter()


@router.get("/docs/", include_in_schema=False, dependencies=[Depends(admin_required)])
def custom_swagger_ui():
    return get_swagger_ui_html(openapi_url="/openapi.json/", title="Docs")


@router.get("/redoc/", include_in_schema=False, dependencies=[Depends(admin_required)])
def custom_redoc_html():
    return get_redoc_html(openapi_url="/openapi.json/", title="Redoc")


@router.get(
    "/openapi.json/",
    include_in_schema=False,
    dependencies=[Depends(admin_required)],
)
def custom_openapi() -> Dict[str, Any]:
    from src.main import app

    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
