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


def test_admin_get_orders_success(client_admin, order_fixture):
    response = client_admin.get(f"{URL_PREFIX}orders/")
    data = response.json()
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "orders" in data
    assert len(data["orders"]) == 1


def test_admin_get_orders_filter_by_user_id(client_admin, order_fixture):
    first_response = client_admin.get(
        f"{URL_PREFIX}orders/?user_id={order_fixture.user_id}"
    )
    data = first_response.json()
    assert first_response.status_code == 200, "Expected status code 200 OK."
    assert "orders" in data
    assert len(data["orders"]) == 1

    second_response = client_admin.get(f"{URL_PREFIX}orders/?user_id=99")
    data = second_response.json()
    assert second_response.status_code == 200, "Expected status code 200 OK."
    assert "orders" in data
    assert len(data["orders"]) == 0


def test_admin_get_orders_filter_by_status(client_admin, order_paid_fixture):
    response = client_admin.get(f"{URL_PREFIX}orders/?status=paid")
    data = response.json()
    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(data["orders"]) == 1
    assert data["orders"][0]["status"] == "paid"

    second_response = client_admin.get(f"{URL_PREFIX}orders/?status=pending")
    data = second_response.json()
    assert second_response.status_code == 200, "Expected status code 200 OK."
    assert len(data["orders"]) == 0


def test_admin_get_orders_invalid_date_format(client_admin):
    response = client_admin.get(f"{URL_PREFIX}orders/?created_at=2023/01/01")

    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Invalid date format. Use YYYY-MM-DD"


def test_admin_get_orders_invalid_status(client_admin):
    response = client_admin.get(f"{URL_PREFIX}orders/?status=invalid_status")

    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert (
        response.json()["detail"]
        == "Invalid status value. Allowed values: ['pending', 'paid', 'cancelled']"
    )


def test_admin_get_payments_success(client_admin, payment_fixture):
    response = client_admin.get(f"{URL_PREFIX}payments/")
    data = response.json()
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "payments" in data
    assert len(data["payments"]) == 1


def test_admin_get_payments_filter_by_email(client_admin, payment_fixture):
    user = payment_fixture.user
    response = client_admin.get(f"{URL_PREFIX}payments/?email={user.email}")
    data = response.json()
    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(data["payments"]) == 1

    response = client_admin.get(f"{URL_PREFIX}payments/?email=nonexistent@test.com")
    data = response.json()
    assert len(data["payments"]) == 0


def test_admin_get_payments_filter_by_status(client_admin, payment_fixture):
    response = client_admin.get(f"{URL_PREFIX}payments/?status=successful")
    data = response.json()
    assert response.status_code == 200, "Expected status code 200 OK."
    assert len(data["payments"]) == 1
    assert data["payments"][0]["status"] == "successful"

    response = client_admin.get(f"{URL_PREFIX}payments/?status=cancelled")
    data = response.json()
    assert len(data["payments"]) == 0


def test_admin_get_payments_invalid_date_format(client_admin):
    response = client_admin.get(f"{URL_PREFIX}payments/?created_at=2023/01/01")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Invalid date format. Use YYYY-MM-DD"


def test_admin_get_payments_invalid_status(client_admin):
    response = client_admin.get(f"{URL_PREFIX}payments/?status=invalid_status")
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Invalid status value. Allowed values: ['successful', 'cancelled', 'refunded']"
    )


# user cannot access tests


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


def test_user_get_orders_forbidden(client_user):
    response = client_user.get(f"{URL_PREFIX}orders/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."


def test_user_get_payments_forbidden(client_user):
    response = client_user.get(f"{URL_PREFIX}payments/")
    assert response.status_code == 403, "Expected status code 403 Forbidden."
    assert response.json()["detail"] == "Access denied. Admin privileges required."
