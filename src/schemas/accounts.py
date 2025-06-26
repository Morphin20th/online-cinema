from pydantic import BaseModel, ConfigDict, field_validator

from ._mixins import EmailMixin, PasswordMixin
from src.validation import password_validation


# --- Request ---
class UserRegistrationRequestSchema(EmailMixin, PasswordMixin, BaseModel):
    pass


class UserLoginRequestSchema(EmailMixin, PasswordMixin, BaseModel):
    pass


class ChangePasswordRequestSchema(EmailMixin, BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return password_validation(value)


class PasswordResetRequestSchema(EmailMixin, BaseModel):
    pass


class PasswordResetCompleteRequestSchema(EmailMixin, PasswordMixin, BaseModel):
    token: str


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class ActivateRequestSchema(EmailMixin, BaseModel):
    token: str


class LogoutRequestSchema(BaseModel):
    refresh_token: str


class EmailRequestSchema(EmailMixin, BaseModel):
    pass


# --- Response ---
class UserRegistrationResponseSchema(EmailMixin, BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
