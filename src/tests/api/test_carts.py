from sqlalchemy.exc import SQLAlchemyError

from src.database import (
    CartItemModel,
    PurchaseModel,
    OrderModel,
    OrderStatusEnum,
    OrderItemModel,
    MovieModel,
)

URL_PREFIX = "cart/"
MOVIE_UUID = {"movie_uuid": "123e4567-e89b-12d3-a456-426655440000"}


def test_get_cart_success(client_cart):
    client, _ = client_cart

    response = client.get(URL_PREFIX)
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "cart_items" in response.json()


def test_anon_get_cart_unauthorized(client):
    response = client.get(URL_PREFIX)
    assert response.status_code == 401, "Expected status code 401 Unauthorized."
    assert response.json()["detail"] == "Authorization header is missing"


def test_add_movie_to_cart_success(client_cart, db_session, movie_fixture):
    client, cart = client_cart

    payload = {"movie_uuid": str(movie_fixture.uuid)}
    response = client.post(f"{URL_PREFIX}add/", json=payload)
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Movie has been added to cart successfully."

    cart_item_record = (
        db_session.query(CartItemModel)
        .filter_by(cart_id=cart.id, movie_id=movie_fixture.id)
        .first()
    )
    assert cart_item_record, "Cart item was not created."


def test_add_movie_to_cart_movie_not_found(client_cart):
    client, cart = client_cart

    response = client.post(f"{URL_PREFIX}add/", json=MOVIE_UUID)
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Movie with given UUID was not found."


def test_add_movie_to_cart_not_found(client_user, movie_fixture):
    response = client_user.post(f"{URL_PREFIX}add/", json=MOVIE_UUID)
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Cart not found."


def test_add_movie_to_cart_bad_request_purchased(
    client_cart, movie_fixture, purchased_movie_fixture, db_session
):
    client, cart = client_cart
    user = cart.user

    db_session.add(PurchaseModel(user_id=user.id, movie_id=movie_fixture.id))
    db_session.commit()

    response = client.post(
        f"{URL_PREFIX}add/", json={"movie_uuid": str(movie_fixture.uuid)}
    )

    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert response.json()["detail"] == "Movie already purchased."


def test_add_movie_to_cart_bad_request_order(client_cart, movie_fixture, db_session):
    client, cart = client_cart
    user = cart.user

    order = OrderModel(user_id=user.id, status=OrderStatusEnum.PENDING)
    db_session.add(order)
    db_session.commit()

    order_item = OrderItemModel(order_id=order.id, movie_id=movie_fixture.id)
    db_session.add(order_item)
    db_session.commit()

    response = client.post(
        f"{URL_PREFIX}add/", json={"movie_uuid": str(movie_fixture.uuid)}
    )

    assert response.status_code == 400, "Expected status code 400 Bad Request."
    assert (
        response.json()["detail"]
        == "Movie is currently in the order in the pending status."
    )


def test_add_movie_to_cart_conflict(client_cart_with_item, movie_fixture, db_session):
    client, _ = client_cart_with_item

    response = client.post(
        f"{URL_PREFIX}add/", json={"movie_uuid": str(movie_fixture.uuid)}
    )
    assert response.status_code == 409, "Expected status code 409 Conflict."
    assert response.json()["detail"] == "Movie already in cart."


def test_add_movie_to_cart_internal_server_error(
    client_cart, movie_fixture, db_session, mocker
):
    client, cart = client_cart
    mocker.patch("src.routes.carts.Session.commit", side_effect=SQLAlchemyError)
    response = client.post(
        f"{URL_PREFIX}add/", json={"movie_uuid": str(movie_fixture.uuid)}
    )
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Error occurred during adding movie to a cart."


def test_remove_movie_from_cart_success(
    client_cart_with_item, movie_fixture, db_session
):
    client, cart = client_cart_with_item

    response = client.delete(f"{URL_PREFIX}items/{movie_fixture.uuid}/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Movie removed from cart."

    cart_item_record = (
        db_session.query(CartItemModel)
        .filter_by(cart_id=cart.id, movie_id=movie_fixture.id)
        .first()
    )
    assert not cart_item_record, "Cart item was not removed."


def test_remove_movie_from_cart_not_found_cart(client_user):
    response = client_user.delete(f"{URL_PREFIX}items/{MOVIE_UUID['movie_uuid']}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Cart not found."


def test_remove_movie_from_cart_not_found_movie(client_cart):
    client, _ = client_cart

    response = client.delete(f"{URL_PREFIX}items/{MOVIE_UUID['movie_uuid']}/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Movie not found in cart."


def test_remove_movie_from_cart_internal_server_error(
    client_cart_with_item, movie_fixture, mocker
):
    client, cart = client_cart_with_item

    mocker.patch("src.routes.carts.Session.commit", side_effect=SQLAlchemyError)
    response = client.delete(f"{URL_PREFIX}items/{movie_fixture.uuid}/")
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert (
        response.json()["detail"] == "Error occurred during removing movie from cart."
    )


def test_remove_all_movies_from_cart_success(client_cart, movies_fixture, db_session):
    movies_fixture(3)
    client, cart = client_cart

    movies = db_session.query(MovieModel).all()

    for movie in movies:
        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db_session.add(cart_item)
    db_session.commit()
    db_session.refresh(cart)

    assert len(cart.cart_items) != 0, "Cart is empty."

    response = client.delete(f"{URL_PREFIX}items/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "All movies removed from cart."

    db_session.refresh(cart)
    assert len(cart.cart_items) == 0, "Cart is not empty."


def test_remove_all_movies_from_cart_not_found(client_user):
    response = client_user.delete(f"{URL_PREFIX}items/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "Cart not found."


def test_remove_all_movies_from_cart_internal_server_error(
    client_cart_with_item, mocker
):
    client, _ = client_cart_with_item

    mocker.patch("src.routes.carts.Session.commit", side_effect=SQLAlchemyError)
    response = client.delete(f"{URL_PREFIX}items/")
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert (
        response.json()["detail"] == "Error occurred while removing movies from cart."
    )
