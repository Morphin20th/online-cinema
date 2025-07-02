from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageResponseSchema(BaseModel):
    message: str


class BaseListSchema(BaseModel):
    prev_page: Optional[str] = Field(None)
    next_page: Optional[str] = Field(None)
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class ErrorResponseSchema(BaseModel):
    detail: str
