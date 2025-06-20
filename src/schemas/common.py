from pydantic import BaseModel, ConfigDict


class MessageResponseSchema(BaseModel):
    message: str


class BaseListSchema(BaseModel):
    prev_page: str
    next_page: str
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)
