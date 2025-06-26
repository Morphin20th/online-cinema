from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ._mixins import EmailMixin
from .common import BaseListSchema


# --- Base Model Schemas ---
class MovieSchema(BaseModel):
    uuid: UUID
    name: str
    price: Decimal


class BaseOrderSchema(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Responses ---
class CreateOrderResponseSchema(BaseOrderSchema):
    movies: List[MovieSchema]


class OrderListSchema(BaseListSchema):
    orders: List[BaseOrderSchema]


class AdminOrderSchema(EmailMixin, BaseOrderSchema):
    user_id: int


class AdminOrderListSchema(BaseListSchema):
    orders: List[AdminOrderSchema]
