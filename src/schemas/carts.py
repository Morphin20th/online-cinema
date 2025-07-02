from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# --- Base Model Schemas ---
class BaseCartItemSchema(BaseModel):
    movie_uuid: UUID
    cart_id: int

    model_config = ConfigDict(from_attributes=True)


class BaseCartSchema(BaseModel):
    cart_items: List["CartItemResponseSchema"]


# ---Requests---
class AddMovieToCartRequestSchema(BaseModel):
    movie_uuid: UUID


# ---Responses---
class CartItemResponseSchema(BaseCartItemSchema):
    movie_name: str
    added_at: datetime
