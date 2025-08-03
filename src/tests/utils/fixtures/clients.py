from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database import UserModel, UserProfileModel, RefreshTokenModel
from src.security import JWTAuthInterface
from src.tests.utils.utils import make_user_payload


def _get_access_token(user_id: int, jwt_manager: JWTAuthInterface) -> str:
    return jwt_manager.create_access_token(data={"user_id": user_id})


@pytest.fixture
def token():
    return "test.token.value"


@pytest.fixture
def user_client_and_user(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_user

    user = create_user(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def admin_client_and_user(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_admin

    user = create_admin(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def moderator_client_and_user(
    client: TestClient, jwt_manager: JWTAuthInterface, db_session
) -> Tuple[TestClient, UserModel]:
    from src.tests.utils.factories import create_moderator

    user = create_moderator(db_session, jwt_manager)
    token = _get_access_token(user.id, jwt_manager)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client, user


@pytest.fixture
def inactive_user_and_payload(
    client: TestClient, db_session: Session
) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    return payload, user


@pytest.fixture
def inactive_user(inactive_user_and_payload) -> UserModel:
    _, user = inactive_user_and_payload
    return user


@pytest.fixture
def active_user_and_payload(
    client: TestClient, db_session: Session
) -> Tuple[dict, UserModel]:
    payload = make_user_payload()
    client.post("accounts/register", json=payload)
    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    user.is_active = True
    db_session.commit()
    return payload, user


@pytest.fixture
def active_user(active_user_and_payload) -> UserModel:
    _, user = active_user_and_payload
    return user


@pytest.fixture
def regular_user(db_session: Session, jwt_manager, settings) -> UserModel:
    user = UserModel.create(
        group_id=2, email="test1@test.com", new_password="Test1234!"
    )
    user.is_active = True
    db_session.add(user)
    db_session.commit()
    profile = UserProfileModel(
        user_id=user.id,
        first_name="Original",
        last_name="User",
        info="Regular user profile",
    )
    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})
    refresh_token = RefreshTokenModel.create(
        user_id=user.id, token=jwt_refresh_token, days=settings.LOGIN_DAYS
    )
    db_session.add_all([profile, refresh_token])
    db_session.commit()
    return user


@pytest.fixture
def client_user(user_client_and_user) -> TestClient:
    client, _ = user_client_and_user
    return client


@pytest.fixture
def client_moderator(moderator_client_and_user) -> TestClient:
    client, _ = moderator_client_and_user
    return client


@pytest.fixture
def client_admin(admin_client_and_user) -> TestClient:
    client, _ = admin_client_and_user
    return client
