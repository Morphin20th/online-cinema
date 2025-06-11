from pydantic import EmailStr, field_serializer, field_validator, Field

from src.validation import password_validation


class EmailMixin:
    email: EmailStr

    @field_serializer("email")
    def serialize_email(self, value: str) -> str:
        return value.lower()


class PasswordMixin:
    password: str = Field(min_length=8, max_length=32)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return password_validation(value)
