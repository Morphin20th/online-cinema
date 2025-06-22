import logging
import smtplib
from datetime import datetime
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr, AnyUrl


class EmailSendingError(Exception):
    pass


class EmailSender:
    def __init__(
        self,
        email_host: str,
        email_port: int,
        email_host_user: str,
        from_email: str,
        app_url: AnyUrl,
        project_root: Path,
    ):
        self._email_host = email_host
        self._email_port = email_port
        self._email_host_user = email_host_user
        self._from_email = from_email
        self._app_url = app_url

        templates_dir = project_root / "src" / "services" / "templates"
        self._env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
        )

    def _render(self, template_name: str, **context) -> str:
        template = self._env.get_template(f"emails/{template_name}.html")
        context.update(
            {
                "year": datetime.now().year,
            }
        )
        return template.render(**context)

    def _send_email(self, to_email: EmailStr, subject: str, html_body: str):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg.set_content(html_body, subtype="html")

        try:
            with smtplib.SMTP(self._email_host, self._email_port) as smtp:
                smtp.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {e}")
            raise EmailSendingError(str(e))

    def send_activation_email(self, to_email: EmailStr, token: str):
        subject = "Account Activation"
        activation_api_url = f"{self._app_url}/accounts/activate/"
        html = self._render(
            "activation",
            subject=subject,
            email=to_email,
            token=token,
            activation_api_url=activation_api_url,
        )

        self._send_email(to_email, subject, html)

    def send_password_reset_email(self, to_email: EmailStr, token: str):
        subject = "Password Reset Request"
        reset_api_url = f"{self._app_url}/accounts/reset-password/complete/"
        html = self._render(
            "password_reset_request",
            subject=subject,
            email=to_email,
            token=token,
            reset_api_url=reset_api_url,
        )
        self._send_email(to_email, subject, html)

    def send_activation_confirmation_email(self, to_email: EmailStr):
        subject = "Account Activated"
        html = self._render(
            "activation_confirmation",
            subject=subject,
            email=to_email,
        )
        self._send_email(to_email, subject, html)

    def send_password_reset_complete_email(self, to_email: EmailStr):
        subject = "Password Reset Complete"
        html = self._render(
            "password_reset_completion",
            subject=subject,
            email=to_email,
        )
        self._send_email(to_email, subject, html)

    def send_payment_success_email(
        self,
        email: EmailStr,
        order_id: int,
        amount: Decimal,
        date: str,
        payment_id: str,
        items: list[dict],
    ) -> None:
        subject = "Payment Confirmation"
        html = self._render(
            "payment_success",
            subject=subject,
            email=email,
            order_id=order_id,
            amount=amount,
            date=date,
            payment_id=payment_id,
            items=items,
        )
        self._send_email(email, subject, html)
