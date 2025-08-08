from sqlalchemy.exc import SQLAlchemyError

from database import PaymentModel
from src.database import (
    OrderModel,
    MovieModel,
    CartItemModel,
    OrderStatusEnum,
    PaymentStatusEnum,
)

URL_PREFIX = "orders/"


def test_create_order_not_found(client_user, db_session):
    response = client_user.post(f"{URL_PREFIX}create/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Cart not found."

    order = db_session.query(OrderModel).all()
    assert len(order) == 0, "Order was created."


def test_create_order_bad_request_empty(client_cart, db_session):
    client, _ = client_cart

    response = client.post(f"{URL_PREFIX}create/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Cart is empty."

    order = db_session.query(OrderModel).all()
    assert len(order) == 0, "Order was created."


def test_create_order_bad_request_order_exists(
    client_cart, order_fixture, db_session, movies_fixture
):
    movies_fixture(1)
    client, cart = client_cart

    movie = db_session.query(MovieModel).filter_by(id=2).first()
    cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    db_session.commit()

    response = client.post(f"{URL_PREFIX}create/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "You already have an unpaid (pending) order."

    orders = db_session.query(OrderModel).all()
    assert len(orders) == 1, "Order was created."


def test_create_order_internal_server_error(client_cart_with_item, db_session, mocker):
    client, _ = client_cart_with_item

    mocker.patch("src.routes.orders.Session.commit", side_effect=SQLAlchemyError)
    response = client.post(f"{URL_PREFIX}create/")
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert (
        response.json()["detail"] == "Error occurred while trying to create an order."
    )
    orders = db_session.query(OrderModel).all()
    assert len(orders) == 0, "Order was created."


def test_create_order_success(client_cart_with_item, db_session):
    client, cart = client_cart_with_item

    response = client.post(f"{URL_PREFIX}create/")
    assert response.status_code == 201, "Expected status code 200 Created."
    data = response.json()
    assert "status" in data and "total_amount" in data and "movies" in data
    assert data["status"] == OrderStatusEnum.PENDING.value
    assert len(data["movies"]) == 1

    order_record = db_session.query(OrderModel).filter_by(user_id=cart.user_id).first()
    assert order_record, "Order was not created."


def test_get_orders_success(client_user, order_fixture, db_session):
    response = client_user.get(URL_PREFIX)
    assert response.status_code == 200, "Expected status code 200."
    data = response.json()
    assert "orders" in data
    assert (
        "total_pages" in data
        and "total_items" in data
        and "prev_page" in data
        and "next_page" in data
    ), "Response expected to have pagination args."

    assert len(response.json()["orders"]) == 1


def test_cancel_order_success(client_user, order_fixture, db_session):
    response = client_user.post(f"{URL_PREFIX}cancel/{order_fixture.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Order successfully cancelled."

    db_session.refresh(order_fixture)

    assert (
        order_fixture.status == OrderStatusEnum.CANCELLED
    ), "Order was not cancelled. "


def test_cancel_order_not_found(client_user, db_session):
    response = client_user.post(f"{URL_PREFIX}cancel/1/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Order with given ID was not found."


def test_cancel_order_conflict_paid(client_user, order_fixture, db_session):
    order_fixture.status = OrderStatusEnum.PAID
    db_session.commit()
    db_session.refresh(order_fixture)

    response = client_user.post(f"{URL_PREFIX}cancel/{order_fixture.id}/")
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert (
        response.json()["detail"]
        == "Paid orders cannot be cancelled. Please request a refund."
    )

    order_record = db_session.query(OrderModel).filter_by(id=order_fixture.id).first()
    assert order_record.status != OrderStatusEnum.PENDING


def test_cancel_order_conflict_cancelled(client_user, order_fixture, db_session):
    order_fixture.status = OrderStatusEnum.CANCELLED
    db_session.commit()
    db_session.refresh(order_fixture)

    response = client_user.post(f"{URL_PREFIX}cancel/{order_fixture.id}/")
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert response.json()["detail"] == "Order is already cancelled."


def test_cancel_order_internal_server_error(
    client_user, order_fixture, db_session, mocker
):
    mocker.patch("src.routes.orders.Session.commit", side_effect=SQLAlchemyError)
    response = client_user.post(f"{URL_PREFIX}cancel/{order_fixture.id}/")
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert (
        response.json()["detail"] == "Error occurred while trying to cancel the order."
    )


def test_refund_order_success(
    client_stripe_mock,
    order_paid_fixture,
    payment_fixture,
    stripe_service_mock,
    db_session,
):
    response = client_stripe_mock.post(f"{URL_PREFIX}refund/{order_paid_fixture.id}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json() == {"message": "Order successfully refunded."}

    db_session.refresh(order_paid_fixture)
    db_session.refresh(payment_fixture)
    assert order_paid_fixture.status == OrderStatusEnum.CANCELLED
    assert payment_fixture.status == PaymentStatusEnum.REFUNDED


def test_refund_order_not_found(client_user):
    response = client_user.post(f"{URL_PREFIX}refund/999999/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Order with given ID was not found."


def test_refund_order_not_paid(client_user, order_fixture):
    response = client_user.post(f"{URL_PREFIX}refund/{order_fixture.id}/")
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert response.json()["detail"] == "Order is not paid."


def test_refund_order_cancelled(client_user, db_session, order_fixture):
    order_fixture.status = OrderStatusEnum.CANCELLED
    db_session.commit()

    response = client_user.post(f"{URL_PREFIX}refund/{order_fixture.id}/")
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert response.json()["detail"] == "Cancelled orders cannot be refunded."


def test_refund_order_missing_payment(client_user, db_session, order_paid_fixture):
    db_session.query(PaymentModel).filter_by(order_id=order_paid_fixture.id).delete()
    db_session.commit()

    response = client_user.post(f"{URL_PREFIX}refund/{order_paid_fixture.id}/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "No valid payment found to refund."


def test_refund_order_no_external_payment_id(client_user, payment_fixture, db_session):
    payment_fixture.external_payment_id = None
    db_session.commit()

    response = client_user.post(f"{URL_PREFIX}refund/{payment_fixture.order_id}/")
    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "No valid payment found to refund."
