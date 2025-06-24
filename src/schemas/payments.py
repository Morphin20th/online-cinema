from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, AnyUrl, ConfigDict

from src.schemas._mixins import EmailMixin
from src.schemas.common import BaseListSchema


class CheckoutResponseSchema(BaseModel):
    checkout_url: AnyUrl


class BasePaymentSchema(BaseModel):
    created_at: datetime
    amount: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class PaymentListItemSchema(EmailMixin, BasePaymentSchema):
    pass


class PaymentsListResponseSchema(BaseListSchema):
    payments: List[BasePaymentSchema]


class AdminPaymentsListResponseSchema(BaseListSchema):
    payments: List[PaymentListItemSchema]
