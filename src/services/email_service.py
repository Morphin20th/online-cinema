import logging
import smtplib
from email.message import EmailMessage

from pydantic import EmailStr


class EmailSender:
    def __init__(
        self,
        # email_host_password: str,
        email_host: str,
        email_port: int,
        email_host_user: str,
        from_email: str,
    ):
        # self._email_host_password = email_host_password
        self._email_host = email_host
        self._email_port = email_port
        self._email_host_user = email_host_user
        self._from_email = from_email

    def _send_email(
        self,
        to_email: EmailStr,
        subject: str,
        body: str,
    ) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self._from_email
        msg["To"] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(self._email_host, self._email_port) as smtp:
                smtp.send_message(msg)
        except smtplib.SMTPException as error:
            logging.error(f"Failed to send email to {to_email}: {error}")
            raise EmailSendingError(f"Failed to send email to {to_email}: {error}")

    def send_activation_email(
        self, to_email: EmailStr, activation_link: str, token: str
    ) -> None:
        link = f"{activation_link}?email={to_email}&token={token}"
        body = "Welcome! Please activate your account using the link below:\n" f"{link}"
        self._send_email(to_email, "Account activation", body)

    def send_activation_confirmation_email(self, to_email: EmailStr) -> None:
        body = (
            "Your account has been successfully activated!\n"
            "Thank you for confirming your email address."
        )
        self._send_email(to_email, "Account activated", body)


class EmailSendingError(Exception):
    pass
