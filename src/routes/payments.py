from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    BackgroundTasks,
    Depends,
    Query,
    status,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

from src.database import (
    OrderModel,
    OrderStatusEnum,
    UserModel,
    PaymentItemModel,
    PaymentStatusEnum,
    PaymentModel,
    PurchaseModel,
    get_db,
)
from src.dependencies import get_current_user, get_stripe_service, get_email_sender
from src.schemas import (
    CURRENT_USER_EXAMPLES,
    STRIPE_ERRORS_EXAMPLES,
    MessageResponseSchema,
    CheckoutResponseSchema,
    PaymentsListResponseSchema,
    BasePaymentSchema,
)
from src.services import StripeServiceInterface, EmailSenderInterface
from src.utils import Paginator, aggregate_error_examples

router = APIRouter()


@router.post(
    "/checkout-session/",
    response_model=CheckoutResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Create Stripe Checkout Session",
    description="Endpoint for creating Stripe checkout session",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user."},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_order_found": "No pending order found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Something went wrong."},
        ),
    },
)
def create_checkout_session(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    stripe_service: StripeServiceInterface = Depends(get_stripe_service),
) -> CheckoutResponseSchema:
    """Create a Stripe Checkout session for the user's pending order.

    Args:
        db: Database session.
        current_user: Authenticated user.
        stripe_service: Stripe service for session creation.

    Returns:
        Checkout URL for Stripe session.
    """
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )

    return CheckoutResponseSchema(checkout_url=checkout_url)


@router.get(
    "/success/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Stripe Success",
    description="Stripe success endpoint",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Payment was successful! Thank you!"},
        ),
    },
)
def return_success():
    return MessageResponseSchema(message="Payment was successful! Thank you!")


@router.get(
    "/cancel/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Stripe Cancel",
    description="Stripe cancel endpoint",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Payment was cancelled."},
        ),
    },
)
def return_cancel() -> MessageResponseSchema:
    return MessageResponseSchema(message="Payment was cancelled.")


@router.post(
    "/webhook/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Stripe Webhook",
    description="Endpoint to handle Stripe webhook events",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Webhook handled"},
        ),
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request", examples={**STRIPE_ERRORS_EXAMPLES}
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_order_found": "Order not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Something went wrong.",
                "cancel": "Error occurred while cancelling expired order.",
            },
        ),
    },
)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    stripe_service: StripeServiceInterface = Depends(get_stripe_service),
    email_manager: EmailSenderInterface = Depends(get_email_sender),
) -> MessageResponseSchema:
    """Handle Stripe webhook events for payment processing.

    Args:
        request: HTTP request object.
        background_tasks: Background tasks manager.
        db: Database session.
        stripe_service: Stripe service for webhook handling.
        email_manager: Email service for notifications.

    Returns:
        Message response indicating webhook handling status.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = stripe_service.parse_webhook_event(payload=payload, sig_header=sig_header)

    event_type = event["type"]
    session = event["data"]["object"]

    if event_type == "checkout.session.completed":
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
    elif event_type == "checkout.session.expired":
        metadata = session.get("metadata", {})
        order_id = metadata.get("order_id")
        if order_id:
            order = db.query(OrderModel).filter_by(id=int(order_id)).first()
            if order and order.status == OrderStatusEnum.PENDING:
                try:
                    payment = PaymentModel(
                        user_id=order.user_id,
                        order_id=order.id,
                        amount=order.total,
                        external_payment_id=session.get("id"),
                        status=PaymentStatusEnum.CANCELLED,
                    )
                    db.add(payment)

                    order.status = OrderStatusEnum.CANCELLED
                    db.commit()

                except SQLAlchemyError:
                    db.rollback()
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error occurred while cancelling expired order.",
                    )

    elif event_type == "payment_intent.payment_failed":
        intent = session
        failure_reason = intent.get("last_payment_error", {}).get(
            "message", "Unknown reason"
        )
        print(
            f"Payment failed for user={intent.get('client_reference_id')}: {failure_reason}"
        )

    return MessageResponseSchema(message="Webhook handled")


@router.get(
    "/",
    response_model=PaymentsListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Payments",
    description="Endpoint for getting user payments",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user."},
        ),
    },
)
def get_payments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentsListResponseSchema:
    """Get paginated list of payments for authenticated user.

    Args:
        request: HTTP request object.
        page: Page number for pagination.
        per_page: Number of items per page.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        Paginated list of payments.
    """
    query = (
        db.query(PaymentModel)
        .filter(PaymentModel.user_id == current_user.id)
        .order_by(PaymentModel.created_at.desc())
    )

    paginator = Paginator(request, query, page, per_page)
    payments = paginator.paginate().all()

    prev_page, next_page = paginator.get_links()

    return PaymentsListResponseSchema(
        payments=(BasePaymentSchema.model_validate(payment) for payment in payments),
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
