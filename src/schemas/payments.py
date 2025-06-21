from pydantic import BaseModel, AnyUrl


class CheckoutResponseSchema(BaseModel):
    checkout_url: AnyUrl
