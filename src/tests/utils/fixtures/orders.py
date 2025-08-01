import pytest

from src.database import (
    OrderModel,
    CartModel,
    OrderItemModel,
    OrderStatusEnum,
    PurchaseModel,
    PaymentModel,
    PaymentStatusEnum,
)


def _create_order(cart: CartModel) -> OrderModel:
    order_items = [OrderItemModel(movie_id=item.movie_id) for item in cart.cart_items]
    order = OrderModel(
        user_id=cart.user_id,
        status=OrderStatusEnum.PENDING,
        order_items=order_items,
    )
    return order


@pytest.fixture
def order_fixture(client_cart_with_item, db_session) -> OrderModel:
    _, cart = client_cart_with_item

    order = _create_order(cart)
    order.total_amount = order.total
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def order_paid_fixture(order_fixture, db_session) -> OrderModel:
    order_fixture.status = OrderStatusEnum.PAID
    db_session.commit()
    db_session.refresh(order_fixture)

    return order_fixture
