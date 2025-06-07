from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    field_serializer,
    field_validator,
    Field,
)


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
        if (
            not any(c.islower() for c in value)
            or not any(c.isupper() for c in value)
            or not any(c.isdigit() for c in value)
            or not any(c in "@$!%*?&" for c in value)
        ):
            raise ValueError(
                "Password must contain 8-32 characters, "
                "at least one uppercase and lowercase letter, "
                "a number and a special character"
            )
        return value


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
