from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MovieSchema(BaseModel):
    uuid: UUID
    name: str
    price: Decimal


class CreateOrderResponseSchema(BaseModel):
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    movies: List[MovieSchema]

    model_config = ConfigDict(from_attributes=True)
