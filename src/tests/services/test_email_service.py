import pytest

from src.services import EmailSender


@pytest.fixture
def email_sender(tmp_path, settings):
    return EmailSender(
        email_host="smtp.example.com",
        email_port=587,
        email_host_user="noreply@example.com",
        from_email="noreply@example.com",
        app_url=f"{settings.APP_URL}",
        project_root=tmp_path,
    )


def assert_email_sent(
    method_to_test,
    expected_template: str,
    expected_subject: str,
    render_kwargs: dict,
    email_sender,
    mocker,
):
    mock_smtp = mocker.patch("smtplib.SMTP")
    mock_render = mocker.patch.object(
        email_sender, "_render", return_value="<html>test</html>"
    )
    mock_smtp_instance = mocker.MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

    method_to_test()

    mock_render.assert_called_once_with(expected_template, **render_kwargs)
    mock_smtp_instance.send_message.assert_called_once()


def test_send_payment_success_email_renders_and_sends(email_sender, mocker):
    to_email = "user@example.com"

    payment_payload = {
        "email": to_email,
        "order_id": 123,
        "amount": 9.99,
        "date": "2025-08-03 15:00",
        "payment_id": "pi_test",
        "items": [{"name": "Movie", "price": 9.99}],
    }

    def call():
        email_sender.send_payment_success_email(**payment_payload)

    assert_email_sent(
        method_to_test=call,
        expected_template="payment_success",
        expected_subject="Payment Confirmation",
        render_kwargs={"subject": "Payment Confirmation", **payment_payload},
        email_sender=email_sender,
        mocker=mocker,
    )


def test_send_activation_email(email_sender, mocker, settings):
    token = "abc123"
    to_email = "user@example.com"

    def call():
        email_sender.send_activation_email(to_email=to_email, token=token)

    assert_email_sent(
        method_to_test=call,
        expected_template="activation",
        expected_subject="Account Activation",
        render_kwargs={
            "subject": "Account Activation",
            "email": to_email,
            "token": token,
            "activation_api_url": f"{settings.APP_URL}accounts/activate/",
        },
        email_sender=email_sender,
        mocker=mocker,
    )


def test_send_password_reset_email(email_sender, mocker, settings):
    token = "abc123"
    to_email = "user@example.com"

    def call():
        email_sender.send_password_reset_email(to_email=to_email, token=token)

    assert_email_sent(
        method_to_test=call,
        expected_template="password_reset_request",
        expected_subject="Password Reset Request",
        render_kwargs={
            "subject": "Password Reset Request",
            "email": to_email,
            "token": token,
            "reset_api_url": f"{settings.APP_URL}accounts/reset-password/complete/",
        },
        email_sender=email_sender,
        mocker=mocker,
    )


def test_send_activation_confirmation_email(email_sender, mocker):
    to_email = "user@example.com"

    def call():
        email_sender.send_activation_confirmation_email(to_email=to_email)

    assert_email_sent(
        method_to_test=call,
        expected_template="activation_confirmation",
        expected_subject="Account Activated",
        render_kwargs={"subject": "Account Activated", "email": to_email},
        email_sender=email_sender,
        mocker=mocker,
    )


def test_send_email_raises_on_failure(email_sender, mocker):
    mocker.patch("smtplib.SMTP", side_effect=Exception("SMTP error"))
    mocker.patch.object(email_sender, "_render", return_value="<html>test</html>")

    with pytest.raises(Exception):
        email_sender.send_password_reset_complete_email("user@example.com")
