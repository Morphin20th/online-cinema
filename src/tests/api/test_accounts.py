from datetime import timezone, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database import UserModel, ActivationTokenModel, CartModel

PASSWORD_ERROR = (
    "Password must contain 8-32 characters, "
    "at least one uppercase and lowercase letter, "
    "a number and a special character"
)


def test_register_user_success(client, db_session, settings):
    assert db_session.query(UserModel).count() == 0

    payload = {"password": "Test1234!", "email": "test@user.com"}
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
    payload = {"email": "test@user.com", "password": invalid_password}
    response = client.post("accounts/register", json=payload)

    assert response.status_code == 422, "Expected status code 422 for invalid password."

    response_data = response.json()
    assert error in str(response_data), f"Expected error message: {error}"


def test_register_user_conflict(client, db_session):
    payload = {"email": "test@user.com", "password": "Test1234!"}
    first_response = client.post("accounts/register", json=payload)
    assert first_response.status_code == 201, "Expected status code 201 Created."

    first_user = db_session.query(UserModel).filter_by(email=payload["email"]).first()
    assert first_user, "User was not created."

    second_response = client.post("accounts/register/", json=payload)
    assert (
        second_response.status_code == 409
    ), "Expected 409 for a duplicate registration."

    response_data = second_response.json()
    expected_message = f"User with this email {payload['email']} already exists."
    assert (
        expected_message == response_data["detail"]
    ), f"Expected error message: {expected_message}"


def test_register_user_internal_server_error(client):
    payload = {"email": "test@user.com", "password": "Test1234!"}

    with patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError):
        response = client.post("accounts/register/", json=payload)

    assert response.status_code == 500, "Expected status code 500 Internal Server Error"
    assert response.json()["detail"] == "An error occurred during user creation."
