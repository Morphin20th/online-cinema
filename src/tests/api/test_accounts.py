from datetime import timezone, datetime, timedelta

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database import (
    UserModel,
    ActivationTokenModel,
    CartModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
)
from src.dependencies import get_redis_client
from src.main import app
from src.tests.utils.utils import make_user_payload

PASSWORD_ERROR = (
    "Password must contain 8-32 characters, "
    "at least one uppercase and lowercase letter, "
    "a number and a special character"
)
PASSWORD = "Test1234!"
INVALID_TOKEN = "invalid_token_value"


def test_register_user_success(client, db_session):
    assert db_session.query(UserModel).count() == 0

    payload = make_user_payload()
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 201, "Expected status code 201 Created."
    response_data = response.json()
    assert response_data["email"] == payload["email"], "Returned email does not match."
    assert "id" in response_data, "Response does not contain user ID."

    user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    assert user, "User was not created."

    activation_token = (
        db_session.query(ActivationTokenModel).filter_by(user_id=user.id).first()
    )
    assert activation_token, "Activation was not created."
    assert activation_token.token, "Activation token has no token."

    expires_at = activation_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    assert expires_at > datetime.now(
        timezone.utc
    ), "Activation token is already expired."

    cart = db_session.query(CartModel).filter_by(user_id=user.id).first()
    assert cart, "Cart was not created."


@pytest.mark.parametrize(
    "invalid_password, error",
    [
        ("ALLUPPERCASE1!", PASSWORD_ERROR),
        ("alllowercase1!", PASSWORD_ERROR),
        ("NoSpecialChar1", PASSWORD_ERROR),
        ("NoDigits!@#", PASSWORD_ERROR),
        ("12345678", PASSWORD_ERROR),
        ("Password", PASSWORD_ERROR),
        ("pass1234", PASSWORD_ERROR),
        ("PASS1234!", PASSWORD_ERROR),
    ],
)
def test_register_user_password_validation(client, invalid_password, error):
    payload = make_user_payload(password=invalid_password)
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 422, "Expected status code 422 for invalid password."

    response_data = response.json()
    assert error in str(response_data), f"Expected error message: {error}"


def test_register_user_conflict(client, inactive_user_and_payload):
    payload, _ = inactive_user_and_payload
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == f"User with this email {payload['email']} already exists."
    )


def test_register_user_internal_server_error(client, mocker):
    payload = make_user_payload()

    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post("accounts/register/", json=payload)

    assert response.status_code == 500, "Expected status code 500 Internal Server Error"
    assert response.json()["detail"] == "An error occurred during user creation."


def test_activate_user_account_success(client, db_session, inactive_user):
    token = (
        db_session.query(ActivationTokenModel)
        .filter_by(user_id=inactive_user.id)
        .first()
    )
    assert token

    response = client.get(
        f"accounts/activate/?email={inactive_user.email}&token={token.token}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User account activated successfully."

    db_session.refresh(inactive_user)
    assert inactive_user.is_active
    assert inactive_user.activation_token is None


def test_activate_user_account_invalid_token(client, inactive_user):
    response = client.get(
        f"accounts/activate/?email={inactive_user.email}&token=invalid-token"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


def test_resend_activation_success(client, db_session, inactive_user):
    db_session.delete(inactive_user.activation_token)
    db_session.commit()

    response = client.post(
        "accounts/resend-activation", json={"email": inactive_user.email}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "A new activation link has been sent."

    new_token = (
        db_session.query(ActivationTokenModel)
        .filter_by(user_id=inactive_user.id)
        .first()
    )
    assert new_token


def test_resend_activation_already_activated(client, db_session, active_user):
    db_session.delete(active_user.activation_token)
    db_session.commit()

    response = client.post(
        "accounts/resend-activation", json={"email": active_user.email}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User is already activated."


def test_resend_activation_not_found(client):
    response = client.post(
        "accounts/resend-activation", json={"email": "nonexistent@email.com"}
    )
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == f"User with given email nonexistent@email.com not found."
    )


def test_resend_activation_valid(client, inactive_user):
    response = client.post(
        "accounts/resend-activation", json={"email": inactive_user.email}
    )
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Activation token still valid."


def test_resend_activation_internal_server_error(
    client, db_session, inactive_user, mocker
):
    db_session.delete(inactive_user.activation_token)
    db_session.commit()

    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post(
        "accounts/resend-activation", json={"email": inactive_user.email}
    )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "An error occurred while creating the token."


def test_login_user_success(client, db_session, active_user_and_payload):
    register_payload, user = active_user_and_payload

    response = client.post("accounts/login/", json=register_payload)
    assert response.status_code == 200, "Expected status code 200 OK."

    response_data = response.json()
    assert "access_token", "refresh_token" in response_data.keys()
    assert response_data["token_type"] == "bearer"

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    assert refresh_token, "Refresh token was not created."


def test_login_user_unauthorized(client, active_user):
    response = client.post(
        "accounts/login/",
        json={"email": active_user.email, "password": "wRongPassword12!"},
    )
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert response.json()["detail"] == "Invalid email or password."


def test_login_user_forbidden(client, inactive_user_and_payload):
    payload, _ = inactive_user_and_payload
    response = client.post("accounts/login/", json=payload)
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Your account is not activated"


def test_login_user_internal_server_error(client, active_user_and_payload, mocker):
    payload, user = active_user_and_payload

    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post("accounts/login", json=payload)
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "An error occurred while creating the token."


def test_logout_user_success(user_client_and_user, db_session, mock_redis):
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    client, user = user_client_and_user

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    assert refresh_token, "Refresh Token was not created"

    response = client.post(
        "accounts/logout/", json={"refresh_token": refresh_token.token}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Logged out successfully."

    app.dependency_overrides.clear()


def test_logout_user_unauthorized(client, mock_redis):
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    response = client.post("accounts/logout/", json={})
    assert response.status_code == 401, "Expected status code 401 Unauthorized"
    assert response.json()["detail"] == "Authorization header is missing"
    app.dependency_overrides.clear()


def test_logout_user_internal_server_error(
    user_client_and_user, db_session, mock_redis, mocker
):
    app.dependency_overrides[get_redis_client] = lambda: mock_redis
    client, user = user_client_and_user

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    assert refresh_token, "Refresh Token was not created"
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post(
        "accounts/logout/", json={"refresh_token": refresh_token.token}
    )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Failed to logout. Try again."
    app.dependency_overrides.clear()


def test_refresh_token_success(user_client_and_user, db_session):
    client, user = user_client_and_user

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    response = client.post(
        "accounts/refresh/", json={"refresh_token": refresh_token.token}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    response_data = response.json()
    assert response_data["access_token"], "Access Token was not returned."

    new_refresh_token = db_session.query(RefreshTokenModel).filter_by(user_id=user.id)
    assert (
        new_refresh_token != refresh_token
    ), "Expected new refresh token to be created."


def test_refresh_token_not_found(user_client_and_user, db_session):
    client, user = user_client_and_user

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    token = refresh_token.token
    db_session.delete(refresh_token)
    db_session.commit()

    response = client.post("accounts/refresh/", json={"refresh_token": token})
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Refresh token not found."


def test_refresh_token_unauthorized_not_belong(client_user, regular_user, db_session):
    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=regular_user.id).first()
    )
    response = client_user.post(
        "accounts/refresh/",
        json={"refresh_token": refresh_token.token},
    )
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert (
        response.json()["detail"] == "Token does not belong to the authenticated user."
    )


def test_refresh_token_unauthorized_expired(user_client_and_user, db_session):
    client, user = user_client_and_user

    refresh_token = (
        db_session.query(RefreshTokenModel).filter_by(user_id=user.id).first()
    )
    refresh_token.expires_at = refresh_token.expires_at - timedelta(days=2)
    db_session.commit()

    response = client.post(
        "accounts/refresh/", json={"refresh_token": refresh_token.token}
    )
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert response.json()["detail"] == "Refresh token expired."


def test_change_password_success(user_client_and_user):
    client, user = user_client_and_user
    payload = {
        "email": user.email,
        "old_password": PASSWORD,
        "new_password": "Test123!",
    }
    response = client.post("accounts/change-password/", json=payload)

    assert response.status_code == 200, "Expected status code 200 OK."
    response_data = response.json()
    assert response_data["message"] == "Password has been changed successfully!"


def test_change_password_conflict(user_client_and_user):
    client, user = user_client_and_user
    payload = {
        "email": user.email,
        "old_password": PASSWORD,
        "new_password": PASSWORD,
    }
    response = client.post("accounts/change-password/", json=payload)

    assert response.status_code == 409, "Expected status code 200 Conflict."
    response_data = response.json()
    assert response_data["detail"] == "New password cannot be same as the old one."


def test_change_password_internal_server_error(user_client_and_user, mocker):
    client, user = user_client_and_user

    payload = {
        "email": user.email,
        "old_password": PASSWORD,
        "new_password": "Test123!",
    }
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post("accounts/change-password", json=payload)

    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred during new password creation."


def test_reset_password_request_inactive_user(client, inactive_user, db_session):
    response = client.post(
        "accounts/reset-password/request/", json={"email": inactive_user.email}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert (
        response.json()["message"]
        == "If you have an account, you will receive an email with instructions."
    )
    reset_token = (
        db_session.query(PasswordResetTokenModel)
        .filter_by(user_id=inactive_user.id)
        .first()
    )
    assert not reset_token, "Password Reset token was crated."


def test_reset_password_request_active_user(client, active_user, db_session):
    response = client.post(
        "accounts/reset-password/request/", json={"email": active_user.email}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert (
        response.json()["message"]
        == "If you have an account, you will receive an email with instructions."
    )
    reset_token = (
        db_session.query(PasswordResetTokenModel)
        .filter_by(user_id=active_user.id)
        .first()
    )
    assert reset_token, "Password Reset token was not crated."


def test_reset_password_request_internal_server_error(client, active_user, mocker):
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client.post(
        "accounts/reset-password/request/", json={"email": active_user.email}
    )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Something went wrong."


@pytest.fixture
def reset_token(db_session, active_user):
    token_record = PasswordResetTokenModel(user_id=active_user.id)
    db_session.add(token_record)
    db_session.commit()
    return token_record.token


@pytest.fixture
def expired_token(db_session, active_user):
    token_record = PasswordResetTokenModel(
        user_id=active_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db_session.add(token_record)
    db_session.commit()
    return token_record.token


def test_successful_password_reset(client, active_user, reset_token, db_session):
    response = client.post(
        "accounts/reset-password/complete/",
        json={
            "email": active_user.email,
            "token": reset_token,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Your password has been successfully changed!"

    db_session.refresh(active_user)

    token = (
        db_session.query(PasswordResetTokenModel)
        .filter_by(user_id=active_user.id)
        .first()
    )
    assert token is None


def test_reset_password_invalid_email(client, reset_token):
    response = client.post(
        "accounts/reset-password/complete/",
        json={
            "email": "wrong@example.com",
            "token": reset_token,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or token."


def test_reset_password_inactive_user(client, inactive_user, db_session):
    token_record = PasswordResetTokenModel(user_id=inactive_user.id)
    db_session.add(token_record)
    db_session.commit()
    token_value = token_record.token

    response = client.post(
        "/accounts/reset-password/complete/",
        json={
            "email": inactive_user.email,
            "token": token_value,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or token."

    db_session.refresh(inactive_user)
    assert inactive_user.password != PASSWORD


def test_reset_password_invalid_token(client, active_user, reset_token):
    response = client.post(
        "accounts/reset-password/complete/",
        json={
            "email": active_user.email,
            "token": INVALID_TOKEN,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or token."


def test_reset_password_expired_token(client, active_user, expired_token, db_session):
    response = client.post(
        "accounts/reset-password/complete/",
        json={
            "email": active_user.email,
            "token": expired_token,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or token."

    token = (
        db_session.query(PasswordResetTokenModel)
        .filter_by(user_id=active_user.id)
        .first()
    )
    assert token is None
