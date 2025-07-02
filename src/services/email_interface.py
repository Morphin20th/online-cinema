from abc import ABC, abstractmethod
from decimal import Decimal

from pydantic import EmailStr


class EmailSenderInterface(ABC):
    @abstractmethod
    def send_activation_email(self, to_email: EmailStr, token: str) -> None:
        """
        Sends an account activation email to the user with a provided token.

        Parameters:
            to_email (EmailStr): Recipient's email address.
            token (str): Token used to activate the user's account.
        """
        pass

    @abstractmethod
    def send_password_reset_email(self, to_email: EmailStr, token: str) -> None:
        """
        Sends a password-reset email with a token to reset the password.

        Parameters:
            to_email (EmailStr): Recipient's email address.
            token (str): Token to reset the password.
        """
        pass

    @abstractmethod
    def send_activation_confirmation_email(self, to_email: EmailStr) -> None:
        """
        Sends a confirmation email after successful account activation.

        Parameters:
            to_email (EmailStr): Recipient's email address.
        """
        pass

    @abstractmethod
    def send_password_reset_complete_email(self, to_email: EmailStr) -> None:
        """
        Sends a confirmation email that the user's password was successfully reset.

        Parameters:
            to_email (EmailStr): Recipient's email address.
        """
        pass

    @abstractmethod
    def send_payment_success_email(
        self,
        email: EmailStr,
        order_id: int,
        amount: Decimal,
        date: str,
        payment_id: str,
        items: list[dict],
    ) -> None:
        """
        Sends an email confirming successful payment.

        Parameters:
            email (EmailStr): Recipient's email address.
            order_id (int): The ID of the order.
            amount (Decimal): The amount paid.
            date (str): Date of the payment.
            payment_id (str): Unique ID of the payment transaction.
            items (list[dict]): List of items purchased (name, quantity, etc.).
        """
        pass
