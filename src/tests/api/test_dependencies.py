import pytest
from fastapi import HTTPException, Request

from src.dependencies import (
    get_current_user,
    get_token,
    admin_required,
    moderator_or_admin_required,
)


def test_get_current_user_success(
    user_client_and_user, db_session, jwt_manager, mock_redis, mocker
):
    client, user = user_client_and_user

    token = client.headers["Authorization"].split()[1]

    mock_redis.get.return_value = None

    mock_request = mocker.MagicMock(spec=Request)
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


def test_get_current_user_missing_auth_header(mocker):
    mock_request = mocker.MagicMock(spec=Request)
    mock_request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        get_token(mock_request)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authorization header is missing"


def test_get_current_user_invalid_auth_format(mocker):
    mock_request = mocker.MagicMock(spec=Request)
    mock_request.headers = {"Authorization": "InvalidFormat"}

    with pytest.raises(HTTPException) as exc_info:
        get_token(mock_request)

    assert exc_info.value.status_code == 401
    assert (
        exc_info.value.detail
        == "Invalid Authorization header format. Expected 'Bearer <token>'"
    )


def test_get_current_user_blacklisted_token(mocker, client_user, mock_redis):
    token = client_user.headers["Authorization"].split()[1]

    mock_redis.get.return_value = "1"

    mock_request = mocker.MagicMock(spec=Request)
    mock_request.headers = {"Authorization": f"Bearer {token}"}

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token=get_token(mock_request),
            jwt_manager=mocker.MagicMock(),
            db=mocker.MagicMock(),
            redis=mock_redis,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has been blacklisted"


def test_get_current_user_invalid_token(mocker, jwt_manager, mock_redis):
    mock_redis.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            token="invalid.token",
            jwt_manager=jwt_manager,
            db=mocker.MagicMock(),
            redis=mock_redis,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_current_user_inactive_user(
    db_session, jwt_manager, mock_redis, inactive_user
):
    token = jwt_manager.create_access_token(data={"user_id": inactive_user.id})

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


def test_admin_required_with_admin(admin_client_and_user):
    _, user = admin_client_and_user
    assert admin_required(user) == user


def test_admin_required_with_non_admin(user_client_and_user):
    _, user = user_client_and_user
    with pytest.raises(HTTPException) as exc_info:
        admin_required(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied. Admin privileges required."


def test_moderator_or_admin_required_with_admin(admin_client_and_user):
    _, user = admin_client_and_user
    assert moderator_or_admin_required(user) == user


def test_moderator_or_admin_required_with_moderator(moderator_client_and_user):
    _, user = moderator_client_and_user
    assert moderator_or_admin_required(user) == user


def test_moderator_or_admin_required_with_user(user_client_and_user):
    _, user = user_client_and_user
    with pytest.raises(HTTPException) as exc_info:
        moderator_or_admin_required(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied. Moderator or admin required."
