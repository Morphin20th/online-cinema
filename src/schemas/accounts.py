from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    field_serializer,
    field_validator,
    Field,
)

from utils import password_validation


class EmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("email")
    def serialize_email(self, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return password_validation(value)


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserRegistrationRequestSchema(EmailPasswordSchema):
    pass


class TokenRefreshResponseSchema(BaseModel):
    access_token: str
    token_type: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserLoginRequestSchema(EmailPasswordSchema):
    pass


class MessageSchema(BaseModel):
    message: str


class ChangePasswordRequestSchema(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return password_validation(value)
