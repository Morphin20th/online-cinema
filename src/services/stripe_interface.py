from abc import ABC, abstractmethod

import stripe
from pydantic import AnyUrl

from database import OrderModel


class StripeServiceInterface(ABC):
    @staticmethod
    @abstractmethod
    def create_refund(payment_intent_id: str) -> stripe.Refund:
        """
        Create a refund for a given Stripe payment intent.

        Parameters:
            payment_intent_id (str): The ID of the payment intent to refund.
        """
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Parses and verifies a Stripe webhook event.

        Parameters:
            payload (bytes): Raw request body from Stripe.
            sig_header (str): Stripe signature header.

        Returns:
            stripe.Event: The parsed Stripe event.
        """
        pass

    @abstractmethod
    def create_checkout_session(
        self, order: OrderModel, expires_after_minutes: int = 30
    ) -> AnyUrl:
        """
        Creates a Stripe Checkout session for the given order.

        Parameters:
            order (OrderModel): The order instance with items to be purchased.
            expires_after_minutes (int): Minutes until session expires.

        Returns:
            AnyUrl: The URL of the created Stripe Checkout session.
        """
        pass
