from pydantic import AnyUrl

from src.config.config import BaseAppSettings


class APISettings(BaseAppSettings):
    APP_URL: AnyUrl = AnyUrl("http://127.0.0.1:8001")

    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
