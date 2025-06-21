from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm.session import Session
from starlette import status

from src.services import StripeService
from src.database import OrderModel, OrderStatusEnum, UserModel
from src.database.session import get_db
from src.dependencies import get_current_user, get_stripe_service
from src.schemas.common import MessageResponseSchema
from src.schemas.payments import CheckoutResponseSchema

router = APIRouter()


@router.post("/checkout-session/", response_model=CheckoutResponseSchema)
def create_checkout_session(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> CheckoutResponseSchema:
    order = (
        db.query(OrderModel)
        .filter(
            OrderModel.user_id == current_user.id,
            OrderModel.status == OrderStatusEnum.PENDING,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No pending order found."
        )

    try:
        checkout_url = stripe_service.create_checkout_session(order)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    return CheckoutResponseSchema(checkout_url=checkout_url)


@router.get("/success", response_model=MessageResponseSchema)
def return_success():
    return MessageResponseSchema(message="Payment was successful! Thank you!")


@router.get("/cancel", response_model=MessageResponseSchema)
def return_cancel() -> MessageResponseSchema:
    return MessageResponseSchema(message="Payment was cancelled.")
