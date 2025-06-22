from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.params import Depends, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session
from starlette import status

from src.services import StripeService, EmailSender
from src.database import (
    OrderModel,
    OrderStatusEnum,
    UserModel,
    PaymentItemModel,
    PaymentStatusEnum,
    PaymentModel,
    PurchaseModel,
)
from src.database.session import get_db
from src.dependencies import get_current_user, get_stripe_service, get_email_sender
from src.schemas.common import MessageResponseSchema
from src.schemas.payments import (
    CheckoutResponseSchema,
    PaymentsListResponseSchema,
    BasePaymentSchema,
)
from src.utils import build_pagination_links

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


@router.post("/webhook/", response_model=MessageResponseSchema)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
    email_manager: EmailSender = Depends(get_email_sender),
) -> MessageResponseSchema:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = stripe_service.parse_webhook_event(payload=payload, sig_header=sig_header)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = int(session["metadata"]["order_id"])
        stripe_payment_id = session.get("payment_intent")

        order = (
            db.query(OrderModel)
            .options(joinedload(OrderModel.user))
            .filter_by(id=order_id)
            .first()
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        try:
            payment = PaymentModel(
                user_id=order.user_id,
                order_id=order.id,
                amount=order.total,
                external_payment_id=stripe_payment_id,
                status=PaymentStatusEnum.SUCCESSFUL,
            )
            db.add(payment)

            order.status = OrderStatusEnum.PAID

            for item in order.order_items:
                db.add_all(
                    [
                        PaymentItemModel(
                            price_at_payment=item.movie.price,
                            payment=payment,
                            order_item=item,
                        ),
                        PurchaseModel(
                            user_id=order.user_id,
                            movie_id=item.movie_id,
                        ),
                    ]
                )

            db.commit()

        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong.",
            )
        else:
            email_data = {
                "email": order.user.email,
                "order_id": order.id,
                "amount": order.total,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "payment_id": stripe_payment_id,
                "items": [
                    {"name": item.movie.name, "price": item.movie.price}
                    for item in order.order_items
                    if item.movie
                ],
            }

            background_tasks.add_task(
                email_manager.send_payment_success_email, **email_data
            )

    return MessageResponseSchema(message="Webhook handled")


@router.get("/", response_model=PaymentsListResponseSchema)
def get_payments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentsListResponseSchema:
    offset = (page - 1) * per_page

    query = (
        db.query(PaymentModel)
        .filter(PaymentModel.user_id == current_user.id)
        .order_by(PaymentModel.created_at.desc())
    )

    total_items = query.count()

    payments = query.offset(offset).limit(per_page).all()

    total_pages = (total_items + per_page - 1) // per_page
    prev_page, next_page = build_pagination_links(request, page, per_page, total_pages)

    return PaymentsListResponseSchema(
        payments=(BasePaymentSchema.model_validate(payment) for payment in payments),
        total_pages=total_pages,
        prev_page=prev_page,
        next_page=next_page,
        total_items=total_items,
    )
