from decimal import Decimal

from pydantic import EmailStr

from src.services import EmailSenderInterface


class StubEmailService(EmailSenderInterface):
    def send_activation_email(self, to_email: EmailStr, token: str) -> None:
        return None

    def send_password_reset_email(self, to_email: EmailStr, token: str) -> None:
        return None

    def send_activation_confirmation_email(self, to_email: EmailStr) -> None:
        return None

    def send_password_reset_complete_email(self, to_email: EmailStr) -> None:
        return None

    def send_payment_success_email(
        self,
        email: EmailStr,
        order_id: int,
        amount: Decimal,
        date: str,
        payment_id: str,
        items: list[dict],
    ) -> None:
        return None
