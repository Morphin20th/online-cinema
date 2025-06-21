import stripe
from fastapi import HTTPException
from pydantic import AnyUrl
from starlette import status

from src.database.models.orders import OrderModel


class StripeService:
    def __init__(self, api_key: str, webhook_key: str, app_url: AnyUrl):
        self._api_key = api_key
        self._webhook_key = webhook_key
        self.app_url = app_url

        stripe.api_key = self._api_key

    def create_checkout_session(self, order: OrderModel) -> AnyUrl:
        if not order.order_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Order has no items"
            )

        line_items = []
        for item in order.order_items:
            if not item.movie:
                continue

            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item.movie.name,
                        },
                        "unit_amount": int(item.movie.price * 100),
                    },
                    "quantity": 1,
                }
            )

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{self.app_url}/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self.app_url}/payments/cancel",
            metadata={"order_id": str(order.id)},
            client_reference_id=str(order.user_id),
        )
        return AnyUrl(session.url)
