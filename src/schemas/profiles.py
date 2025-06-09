from datetime import date

from pydantic import BaseModel, field_serializer

from database.models.accounts import GenderEnum


class ProfileSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str
    avatar: str

    @field_serializer("first_name", "last_name")
    def serialize_lower(self, value: str) -> str:
        return value.lower()
