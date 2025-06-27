from pathlib import Path

from dotenv import load_dotenv
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

load_dotenv()


class BaseAppSettings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    # Project Structure
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.resolve()

    # App Config
    APP_URL: AnyUrl = "http://127.0.0.1:8001"

    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"

    # will use later
    DEBUG: bool = False
    TESTING: bool = False
