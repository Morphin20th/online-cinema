from datetime import date
from typing import Optional

from pydantic import BaseModel, field_serializer

from src.database.models.enums import GenderEnum


class ProfileSchema(BaseModel):
    id: int
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
    avatar: Optional[str] = None

    @field_serializer("first_name", "last_name")
    def serialize_lower(self, value: str) -> str:
        return value.lower()


ProfileSchema.model_rebuild()
