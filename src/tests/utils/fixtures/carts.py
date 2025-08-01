from typing import Tuple

import pytest
from fastapi.testclient import TestClient

from src.database import CartModel, CartItemModel


@pytest.fixture
def client_cart(db_session, client_user) -> Tuple[TestClient, CartModel]:
    client, user = client_user

    cart = CartModel(user=user)
    db_session.add(cart)
    db_session.commit()

    return client, cart


@pytest.fixture
def client_cart_with_item(
    client_cart, db_session, movie_fixture
) -> Tuple[TestClient, CartModel]:
    client, cart = client_cart
    cart_item = CartItemModel(cart_id=cart.id, movie_id=movie_fixture.id)
    db_session.add(cart_item)
    db_session.commit()
    return client, cart
