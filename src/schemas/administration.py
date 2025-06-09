from pydantic import BaseModel, EmailStr, field_serializer


class BaseEmailSchema(BaseModel):
    email: EmailStr

    @field_serializer("email")
    def serialize_email(self, value: str) -> str:
        return value.lower()


class ChangeGroupRequest(BaseEmailSchema):
    group_id: int
