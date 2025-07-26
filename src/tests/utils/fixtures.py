from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import UserModel
from src.security import JWTAuthInterface
from src.tests.utils.utils import make_user_payload


def _get_access_token(user_id: int, jwt_manager: JWTAuthInterface) -> str:
    return jwt_manager.create_access_token(data={"user_id": user_id})


@pytest.fixture
def token():
    return "test.token.value"


@pytest.fixture
def client_authorized_by_user(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_user

    user = create_user(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def client_authorized_by_admin(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_admin

    user = create_admin(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def client_authorized_by_moderator(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_moderator

    user = create_moderator(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def registered_user(client: TestClient, db_session: Session) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    return payload, user


@pytest.fixture
def registered_and_activated_user(
    client: TestClient, db_session: Session
) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    user.is_active = True
    db_session.commit()
    return payload, user
