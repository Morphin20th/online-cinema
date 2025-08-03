from functools import partial

from sqlalchemy.exc import SQLAlchemyError

from src.database import UserModel
from src.tests.conftest import db_session

URL_PREFIX = "admin/"


def test_admin_activate_user_success(client_admin, inactive_user, db_session):
    response = client_admin.post(
        f"{URL_PREFIX}accounts/activate/", json={"email": inactive_user.email}
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "User account activated successfully by admin."

    db_session.refresh(inactive_user)
    assert inactive_user.is_active, "User account is not active."


def test_admin_activate_user_already_active(client_admin, active_user):
    response = client_admin.post(
        f"{URL_PREFIX}accounts/activate/",
        json={"email": active_user.email},
    )
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "User account is already active."

    assert active_user.is_active, "User account was deactivated."


def test_admin_activate_user_not_found(client_admin, db_session):
    email = "nonexistent@test.com"
    response = client_admin.post(
        f"{URL_PREFIX}accounts/activate/", json={"email": email}
    )
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == f"User with given email {email} not found."


def test_admin_activate_user_internal_server_error(
    client_admin, inactive_user, db_session, mocker
):
    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client_admin.post(
        f"{URL_PREFIX}accounts/activate/", json={"email": inactive_user.email}
    )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred during user account activation."


def test_admin_change_user_group_success(client_admin, active_user, db_session):
    payload = {"email": active_user.email, "group_id": 3}

    make_request = partial(
        client_admin.post, f"{URL_PREFIX}accounts/change-group/", json=payload
    )

    first_response = make_request()
    assert first_response.status_code == 200, "Expected status code 200 OK."
    assert first_response.json()["message"] == "User group successfully changed to 3."

    db_session.refresh(active_user)
    assert active_user.group_id == 3, "User group was not changed."

    second_response = make_request()
    assert second_response.status_code == 200, "Expected status code 200 OK."
    assert second_response.json()["message"] == "User already belongs to group 3."

    assert active_user.group_id == 3, "User group was changed."


def test_admin_change_user_group_bad_request(client_admin, active_user):
    payload = {"email": active_user.email, "group_id": 10}
    response = client_admin.post(f"{URL_PREFIX}accounts/change-group/", json=payload)
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Invalid group ID."


def test_admin_change_user_group_forbidden(admin_client_and_user, db_session):
    client, admin = admin_client_and_user

    payload = {"email": admin.email, "group_id": 2}
    response = client.post(f"{URL_PREFIX}accounts/change-group/", json=payload)
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert (
        response.json()["detail"]
        == "Prevent changing the group of a user with the same ID as you."
    )
    admin_record = db_session.query(UserModel).filter_by(id=admin.id).first()
    assert admin_record.group_id == admin.group_id, "Group ID was changed."


def test_admin_change_user_group_not_found(client_admin, db_session):
    payload = {"email": "nonexistent@test.com", "group_id": 2}

    response = client_admin.post(f"{URL_PREFIX}accounts/change-group/", json=payload)
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert (
        response.json()["detail"]
        == f"User with given email {payload['email']} not found."
    )


def test_admin_change_user_group_internal_server_error(
    client_admin, active_user, db_session, mocker
):
    payload = {"email": active_user.email, "group_id": 3}

    mocker.patch("sqlalchemy.orm.Session.commit", side_effect=SQLAlchemyError)
    response = client_admin.post(f"{URL_PREFIX}accounts/change-group/", json=payload)
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred during user group changing."


def test_admin_get_user_cart_success(client_admin, active_user, db_session):
    response = client_admin.get(f"{URL_PREFIX}carts/{active_user.id}")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "cart_items" in response.json()


def test_admin_get_user_cart_not_found(client_admin, db_session):
    response = client_admin.get(f"{URL_PREFIX}carts/999/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "User with given ID was not found."


# user cannot access tests TODO: payments, orders


def test_user_activate_specific_user_forbidden(client_user):
    response = client_user.post(
        f"{URL_PREFIX}accounts/activate/", json={"email": "test@email.com"}
    )
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."


def test_user_change_specific_user_group_forbidden(client_user):
    response = client_user.post(
        f"{URL_PREFIX}accounts/change-group/",
        json={"email": "test@email.com", "group_id": 1},
    )
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."


def test_user_get_specific_user_cart_forbidden(client_user):
    response = client_user.get(f"{URL_PREFIX}carts/999/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."
