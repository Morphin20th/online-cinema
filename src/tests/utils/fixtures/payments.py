import pytest
from fastapi.testclient import TestClient

from src.services import StripeService
from src.database import PaymentModel, PaymentStatusEnum
from src.dependencies import get_stripe_service
from src.main import app


@pytest.fixture
def stripe_service(settings):
    return StripeService(
        api_key="sk_test_123",
        webhook_key="whsec_123",
        app_url=f"{settings.APP_URL}",
    )


@pytest.fixture
def stripe_service_mock(mocker):
    mock = mocker.MagicMock()
    mock.create_checkout_session.return_value = "https://fake.stripe.url/session"
    return mock


@pytest.fixture
def stripe_session_failure_mock(mocker):
    mock = mocker.MagicMock()
    mock.create_checkout_session.side_effect = Exception("fail")
    return mock


@pytest.fixture
def stripe_webhook_mock(stripe_service_mock, order_fixture):
    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_fixture.id)},
                "payment_intent": "pi_123456789",
                "customer_email": order_fixture.user.email,
            }
        },
    }

    stripe_service_mock.parse_webhook_event.return_value = fake_event
    return stripe_service_mock


@pytest.fixture
def client_stripe_mock(client_user, stripe_service_mock) -> TestClient:
    app.dependency_overrides[get_stripe_service] = lambda: stripe_service_mock
    yield client_user
    app.dependency_overrides.clear()


@pytest.fixture
def client_stripe_session_failure(
    client_user, stripe_session_failure_mock
) -> TestClient:
    app.dependency_overrides[get_stripe_service] = lambda: stripe_session_failure_mock
    yield client_user
    app.dependency_overrides.clear()


@pytest.fixture
def client_webhook(client_user, stripe_webhook_mock):
    app.dependency_overrides[get_stripe_service] = lambda: stripe_webhook_mock
    yield client_user
    app.dependency_overrides.clear()


@pytest.fixture
def payment_fixture(order_paid_fixture, db_session):
    payment = PaymentModel(
        user_id=order_paid_fixture.user_id,
        order_id=order_paid_fixture.id,
        amount=order_paid_fixture.total,
        external_payment_id="pi_test_12345",
        status=PaymentStatusEnum.SUCCESSFUL,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment
