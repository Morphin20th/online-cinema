import pytest
import stripe
from fastapi import HTTPException

from src.database import OrderModel
from tests.utils.fixtures import stripe_service


def test_create_checkout_session_success(stripe_service, mocker):
    order = mocker.MagicMock(spec=OrderModel)
    order.id = 1
    order.user_id = 2
    order.user.email = "user@example.com"
    order.order_items = [mocker.MagicMock()]
    order.order_items[0].movie.name = "Test Movie"
    order.order_items[0].movie.price = 9.99

    checkout_session_url = "https://stripe-session-url.com/"

    mock_create = mocker.patch("stripe.checkout.Session.create")
    mock_create.return_value.url = checkout_session_url
    url = stripe_service.create_checkout_session(order)

    mock_create.assert_called_once()
    assert str(url) == checkout_session_url


def test_create_checkout_session_empty_order(stripe_service, mocker):
    order = mocker.MagicMock(spec=OrderModel)
    order.order_items = []

    with pytest.raises(HTTPException) as exc:
        stripe_service.create_checkout_session(order)
    assert exc.value.status_code == 400, "Expected status code 400 Bad Request."
    assert exc.value.detail == "Order has no items"


def test_parse_webhook_event_success(stripe_service, mocker):
    mock_event = mocker.MagicMock()
    mock_construct = mocker.patch(
        "stripe.Webhook.construct_event", return_value=mock_event
    )

    result = stripe_service.parse_webhook_event({}, "sig_header")
    assert result == mock_event
    mock_construct.assert_called_once_with(
        payload={}, sig_header="sig_header", secret="whsec_123"
    )


def test_parse_webhook_event_invalid_signature(stripe_service, mocker):
    mocker.patch(
        "stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError("msg", "sig"),
    )

    with pytest.raises(HTTPException) as exc:
        stripe_service.parse_webhook_event({}, "sig_header")

    assert exc.value.status_code == 400, "Expected status code 400 Bad Request."
    assert exc.value.detail == "Invalid Stripe webhook signature."


def test_parse_webhook_event_invalid_payload(stripe_service, mocker):
    mocker.patch("stripe.Webhook.construct_event", side_effect=Exception("bad"))

    with pytest.raises(HTTPException) as exc:
        stripe_service.parse_webhook_event({}, "sig_header")

    assert exc.value.status_code == 400, "Expected status code 400 Bad Request."
    assert exc.value.detail == "Invalid Stripe webhook payload."


def test_create_refund_success(stripe_service, mocker):
    mock_refund = {"id": "re_123"}
    mocker.patch("stripe.Refund.create", return_value=mock_refund)

    result = stripe_service.create_refund("pi_test")
    assert result == mock_refund


def test_create_refund_stripe_error(mocker, stripe_service):
    mocker.patch(
        "stripe.Refund.create",
        side_effect=stripe.error.StripeError(message="Generic Stripe error"),
    )

    with pytest.raises(HTTPException) as exc:
        stripe_service.create_refund("pi_test")

    assert exc.value.status_code == 400, "Expected status code 400 Bad Request."
    assert "Stripe refund error" in str(exc.value.detail)
