from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from dependencies import admin_required, moderator_or_admin_required
from src.dependencies import get_current_user, get_token


def test_get_current_user_success(
    client_authorized_by_user, db_session, jwt_manager, mock_redis
):
    client, user = client_authorized_by_user

    token = client.headers["Authorization"].split()[1]

    mock_redis.get.return_value = None

    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {token}"}

    current_user = get_current_user(
        token=get_token(mock_request),
        jwt_manager=jwt_manager,
        db=db_session,
        redis=mock_redis,
    )

    assert current_user.id == user.id
    assert current_user.email == user.email
    mock_redis.get.assert_called_once_with(f"bl:{token}")


def test_get_current_user_missing_auth_header():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        get_token(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authorization header is missing"


def test_get_current_user_invalid_auth_format():
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "InvalidFormat"}

    with pytest.raises(HTTPException) as exc_info:
        get_token(mock_request)

    assert exc_info.value.status_code == 401
    assert (
        exc_info.value.detail
        == "Invalid Authorization header format. Expected 'Bearer <token>'"
    )


def test_get_current_user_blacklisted_token(client_authorized_by_user, mock_redis):
    client, _ = client_authorized_by_user
    token = client.headers["Authorization"].split()[1]

    mock_redis.get.return_value = "1"

    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {token}"}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=get_token(mock_request),
            jwt_manager=MagicMock(),
            db=MagicMock(),
            redis=mock_redis,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been blacklisted"


def test_get_current_user_invalid_token(jwt_manager, mock_redis):
    mock_redis.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token="invalid.token",
            jwt_manager=jwt_manager,
            db=MagicMock(),
            redis=mock_redis,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_current_user_inactive_user(
    db_session, jwt_manager, mock_redis, registered_user
):
    _, user = registered_user
    token = jwt_manager.create_access_token(data={"user_id": user.id})

    mock_redis.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=token, jwt_manager=jwt_manager, db=db_session, redis=mock_redis
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user."


def test_get_current_user_not_found(db_session, jwt_manager, mock_redis):
    token = jwt_manager.create_access_token(data={"user_id": 999})

    mock_redis.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=token, jwt_manager=jwt_manager, db=db_session, redis=mock_redis
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found."


def test_admin_required_with_admin(client_authorized_by_admin):
    _, user = client_authorized_by_admin
    assert admin_required(user) == user


def test_admin_required_with_non_admin(client_authorized_by_user):
    _, user = client_authorized_by_user
    with pytest.raises(HTTPException) as exc_info:
        admin_required(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied. Admin privileges required"


def test_moderator_or_admin_required_with_admin(client_authorized_by_admin):
    _, user = client_authorized_by_admin
    assert moderator_or_admin_required(user) == user


def test_moderator_or_admin_required_with_moderator(client_authorized_by_moderator):
    _, user = client_authorized_by_moderator
    assert moderator_or_admin_required(user) == user


def test_moderator_or_admin_required_with_user(client_authorized_by_user):
    _, user = client_authorized_by_user
    with pytest.raises(HTTPException) as exc_info:
        moderator_or_admin_required(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied. Moderator or admin required."
