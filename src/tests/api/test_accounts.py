from datetime import timezone, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database import UserModel, ActivationTokenModel, CartModel
from src.tests.utils.utils import make_user_payload

PASSWORD_ERROR = (
    "Password must contain 8-32 characters, "
    "at least one uppercase and lowercase letter, "
    "a number and a special character"
)


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
def test_register_user_password_validation(client, db_session, invalid_password, error):
    payload = make_user_payload(password=invalid_password)
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 422, "Expected status code 422 for invalid password."

    response_data = response.json()
    assert error in str(response_data), f"Expected error message: {error}"


def test_register_user_conflict(client, registered_user):
    payload, _ = registered_user
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == f"User with this email {payload['email']} already exists."
    )


def test_register_user_internal_server_error(client):
    payload = make_user_payload()

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.post("accounts/register/", json=payload)

    assert response.status_code == 500, "Expected status code 500 Internal Server Error"
    assert response.json()["detail"] == "An error occurred during user creation."


def test_activate_user_account_success(client, db_session, registered_user):
    payload, user = registered_user
    token = db_session.query(ActivationTokenModel).filter_by(user_id=user.id).first()
    assert token

    response = client.get(
        f"accounts/activate/?email={payload['email']}&token={token.token}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User account activated successfully."

    db_session.refresh(user)
    assert user.is_active
    assert (
        db_session.query(ActivationTokenModel).filter_by(user_id=user.id).first()
        is None
    )


def test_activate_user_account_invalid_token(client, registered_user):
    payload, _ = registered_user
    response = client.get(
        f"accounts/activate/?email={payload['email']}&token=invalid-token"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


def test_resend_activation_success(client, db_session, registered_user):
    payload, user = registered_user
    db_session.delete(user.activation_token)
    db_session.commit()

    response = client.post(
        "accounts/resend-activation", json={"email": payload["email"]}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "A new activation link has been sent."

    new_token = (
        db_session.query(ActivationTokenModel).filter_by(user_id=user.id).first()
    )
    assert new_token and new_token.token


def test_resend_activation_already_activated(
    client, db_session, registered_and_activated_user
):
    payload, user = registered_and_activated_user
    db_session.delete(user.activation_token)
    db_session.commit()

    response = client.post(
        "accounts/resend-activation", json={"email": payload["email"]}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User is already activated."


def test_resend_activation_internal_server_error(client, db_session, registered_user):
    payload, user = registered_user
    db_session.delete(user.activation_token)
    db_session.commit()

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.post(
            "accounts/resend-activation", json={"email": payload["email"]}
        )

    assert response.status_code == 500
