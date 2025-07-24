from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings, Settings
from src.database import Base, create_postgres_session, load_initial_groups
from src.dependencies import get_jwt_auth_manager
from src.main import app
from src.security import JWTAuthInterface


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def engine(settings: Settings):
    SessionLocal = create_postgres_session(settings)
    return SessionLocal.kw["bind"]


@pytest.fixture(scope="function")
def db_session(settings: Settings) -> Session:
    SessionLocal = create_postgres_session(settings)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def jwt_manager() -> JWTAuthInterface:
    return get_jwt_auth_manager()


@pytest.fixture(scope="session", autouse=True)
def prepare_test_db(engine: sessionmaker, settings: Settings):
    SessionLocal = create_postgres_session(settings)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    load_initial_groups(session)
    session.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _get_access_token(user_id: int, jwt_manager: JWTAuthInterface) -> str:
    return jwt_manager.create_access_token(data={"user_id": user_id})


@pytest.fixture
def client_authorized_by_user(
    client: TestClient, jwt_manager: JWTAuthInterface
) -> TestClient:
    from src.tests.utils.factories import create_user

    user = create_user()
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def client_authorized_by_admin(
    client: TestClient, jwt_manager: JWTAuthInterface
) -> TestClient:
    from src.tests.utils.factories import create_admin

    user = create_admin()
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def client_authorized_by_moderator(
    client: TestClient, jwt_manager: JWTAuthInterface
) -> TestClient:
    from src.tests.utils.factories import create_moderator

    user = create_moderator()
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
