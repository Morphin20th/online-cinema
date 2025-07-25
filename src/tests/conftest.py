import pytest
from fastapi.testclient import TestClient

from dependencies import get_email_sender
from security.token_manager import JWTManager
from src.config import get_settings, Settings
from src.database import reset_database, get_postgres_db_contextmanager
from src.dependencies import get_jwt_auth_manager
from src.main import app
from src.security import JWTAuthInterface
from src.tests.stubs import StubEmailService

from src.tests.utils import *  # noqa


@pytest.fixture
def email_service_stub():
    return StubEmailService()


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    reset_database()


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="function")
def db_session():
    with get_postgres_db_contextmanager() as session:
        yield session


@pytest.fixture(scope="function")
def jwt_manager(settings) -> JWTAuthInterface:
    return JWTManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.ALGORITHM,
    )


@pytest.fixture
def client(email_service_stub):
    app.dependency_overrides[get_email_sender] = lambda: email_service_stub

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
