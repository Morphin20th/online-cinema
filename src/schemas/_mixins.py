from datetime import datetime

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


class YearMixin:
    year: int

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        oldest_movie = 1895
        current_year = datetime.now().year
        if value > current_year + 1:
            raise ValueError(f"Year cannot be in future: {value}")
        if value < oldest_movie:
            raise ValueError(f"Year cannot be before {oldest_movie}")
        return value
