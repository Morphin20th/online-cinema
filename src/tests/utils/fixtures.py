import pytest
from fastapi.testclient import TestClient

from src.security import JWTAuthInterface


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
