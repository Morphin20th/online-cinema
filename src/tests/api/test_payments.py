from src.database import OrderStatusEnum
from src.dependencies import get_stripe_service

URL_PREFIX = "payments/"


def test_create_checkout_session_success(client_stripe_mock, order_fixture):
    client = client_stripe_mock

    response = client.post(f"{URL_PREFIX}checkout-session/")
    assert response.status_code == 200, "Expected status code 200 OK."
    assert "checkout_url" in response.json()
    assert response.json()["checkout_url"] == "https://fake.stripe.url/session"


def test_create_checkout_session_not_found(client_stripe_mock):
    client = client_stripe_mock

    response = client.post(f"{URL_PREFIX}checkout-session/")
    assert response.status_code == 404, "Expected status code 404 Not Found."
    assert response.json()["detail"] == "No pending order found."


def test_create_checkout_session_internal_server_error(
    client_stripe_session_failure, order_fixture, mocker
):
    client = client_stripe_session_failure
    mocker.patch(
        "src.services.stripe.StripeService.create_checkout_session",
        side_effect=Exception("fail"),
    )
    response = client.post(f"{URL_PREFIX}checkout-session/")
    assert (
        response.status_code == 500
    ), "Expected status code 500 Internal Server Error."
    assert response.json()["detail"] == "Something went wrong."


def test_stripe_webhook_checkout_session_completed(
    client_webhook, db_session, order_fixture
):
    headers = {"stripe-signature": "fake_signature"}

    response = client_webhook.post(f"{URL_PREFIX}webhook/", headers=headers)

    assert response.status_code == 200
    assert response.json()["message"] == "Webhook handled"

    db_session.refresh(order_fixture)
    assert order_fixture.status == OrderStatusEnum.PAID


def test_stripe_webhook_checkout_session_expired(
    client_webhook, db_session, order_fixture
):
    payload = {
        "type": "checkout.session.expired",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_fixture.id)},
                "id": "cs_test_expired_123",
            }
        },
    }

    headers = {"stripe-signature": "fake_signature"}

    client_webhook.app.dependency_overrides[
        get_stripe_service
    ]().parse_webhook_event.return_value = payload

    response = client_webhook.post(f"{URL_PREFIX}webhook/", headers=headers)

    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Webhook handled"

    db_session.refresh(order_fixture)
    assert order_fixture.status == OrderStatusEnum.CANCELLED


def test_stripe_webhook_payment_intent_failed(client_webhook):
    payload = {
        "type": "payment_intent.payment_failed",
        "data": {
            "object": {
                "id": "pi_failed_123",
                "client_reference_id": "some_user_id",
                "last_payment_error": {"message": "Card declined"},
            }
        },
    }

    headers = {"stripe-signature": "fake_signature"}

    client_webhook.app.dependency_overrides[
        get_stripe_service
    ]().parse_webhook_event.return_value = payload

    response = client_webhook.post(f"{URL_PREFIX}webhook/", headers=headers)

    assert response.status_code == 200, "Expected status code 200 OK."
    assert response.json()["message"] == "Webhook handled"


def test_get_payments_success(client_user, payment_fixture):
    response = client_user.get(URL_PREFIX)

    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert len(data["payments"]) >= 1

    payment = data["payments"][0]
    assert payment["status"] == "successful"
