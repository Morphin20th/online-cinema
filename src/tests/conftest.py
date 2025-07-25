import pytest
from fastapi.testclient import TestClient

from src.config import get_settings, Settings
from src.database import reset_database, get_postgres_db_contextmanager
from src.dependencies import get_jwt_auth_manager
from src.main import app
from src.security import JWTAuthInterface


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
def jwt_manager() -> JWTAuthInterface:
    return get_jwt_auth_manager()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
