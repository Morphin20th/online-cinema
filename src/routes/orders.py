from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.database import (
    OrderItemModel,
    OrderModel,
    OrderStatusEnum,
    MovieModel,
    CartItemModel,
    UserModel,
    CartModel,
    PaymentModel,
    PaymentStatusEnum,
    PurchaseModel,
)
from src.database.session import get_db
from src.dependencies import get_current_user, get_stripe_service
from src.schemas import (
    CURRENT_USER_EXAMPLES,
    STRIPE_ERRORS_EXAMPLES,
    MessageResponseSchema,
    CreateOrderResponseSchema,
    MovieSchema,
    OrderListSchema,
    BaseOrderSchema,
)
from src.services import StripeServiceInterface
from src.utils import Paginator, aggregate_error_examples

router = APIRouter()


@router.post(
    "/create/",
    response_model=CreateOrderResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order",
    description="Endpoint for creating an order if user has Cart Items.",
    responses={
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "empty_cart": "Cart is empty.",
                "unpaid_order": "You already have an unpaid (pending) order.",
            },
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Inactive user.",
            },
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_cart_found": "Cart not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred while trying to create an order."
            },
        ),
    },
)
def create_order(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
) -> CreateOrderResponseSchema:
    """Create a new order from user's cart if conditions are met.

    Args:
        current_user: Authenticated user making the request.
        db: Database session.

    Returns:
        Order details with list of movies and total amount.
    """
    cart = (
        db.query(CartModel)
        .options(joinedload(CartModel.cart_items).joinedload(CartItemModel.movie))
        .filter(CartModel.user_id == current_user.id)
        .first()
    )

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found."
        )

    if not cart.cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty."
        )

    existing_pending_order = (
        db.query(OrderModel)
        .filter_by(user_id=current_user.id, status=OrderStatusEnum.PENDING)
        .first()
    )
    if existing_pending_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an unpaid (pending) order.",
        )

    movie_ids = [item.movie_id for item in cart.cart_items]

    existing_purchase_count = (
        db.query(func.count(OrderItemModel.id))
        .join(OrderModel)
        .filter(
            OrderModel.user_id == current_user.id,
            OrderModel.status == OrderStatusEnum.PAID,
            OrderItemModel.movie_id.in_(movie_ids),
        )
        .scalar()
    )

    if existing_purchase_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Some movies already purchased"
        )

    try:
        new_order = OrderModel(
            user_id=current_user.id,
            status=OrderStatusEnum.PENDING,
            order_items=[
                OrderItemModel(movie_id=item.movie_id) for item in cart.cart_items
            ],
        )

        total = (
            db.query(func.sum(MovieModel.price))
            .filter(MovieModel.id.in_(movie_ids))
            .scalar()
        )
        new_order.total_amount = total or 0

        db.query(CartItemModel).filter(CartItemModel.cart_id == cart.id).delete()

        db.add(new_order)
        db.commit()
        db.refresh(new_order)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while trying to create an order.",
        )

    order_with_items = (
        db.query(OrderModel)
        .options(joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie))
        .filter(OrderModel.id == new_order.id)
        .first()
    )

    return CreateOrderResponseSchema(
        id=order_with_items.id,
        status=order_with_items.status.value,
        total_amount=order_with_items.total_amount,
        created_at=order_with_items.created_at,
        movies=[
            MovieSchema(
                uuid=item.movie.uuid, name=item.movie.name, price=item.movie.price
            )
            for item in order_with_items.order_items
        ],
    )


@router.get(
    "/",
    response_model=OrderListSchema,
    status_code=status.HTTP_200_OK,
    summary="Get User Orders",
    description="Endpoint for getting user orders",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Inactive user.",
            },
        ),
    },
)
def get_orders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderListSchema:
    """Get paginated list of user orders.

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        per_page: Number of items per page.
        current_user: Authenticated user making the request.
        db: Database session.

    Returns:
        Paginated list of user orders with navigation links.
    """
    query = (
        db.query(OrderModel)
        .filter(OrderModel.user_id == current_user.id)
        .options(joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie))
    )

    paginator = Paginator(request, query, page, per_page)
    orders = paginator.paginate().all()
    prev_page, next_page = paginator.get_links()

    return OrderListSchema(
        orders=[BaseOrderSchema.model_validate(order) for order in orders],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )


@router.post(
    "/cancel/{order_id}/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Cancel Order",
    description="Endpoint for cancelling user order",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK", examples={"message": "Order successfully cancelled."}
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Inactive user.",
            },
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_order_found": "Order with given ID was not found."},
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={
                "paid_orders": "Paid orders cannot be cancelled. Please request a refund.",
                "cancelled": "Order is already cancelled.",
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred while trying to cancel the order."
            },
        ),
    },
)
def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """Cancel user's order if conditions are met.

    Args:
        order_id: ID of the order to cancel.
        current_user: Authenticated user making the request.
        db: Database session.

    Returns:
        Message confirming successful cancellation.
    """
    order = (
        db.query(OrderModel)
        .filter_by(id=order_id, user_id=current_user.id)
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order with given ID was not found.",
        )

    if order.status != OrderStatusEnum.PENDING:
        if order.status == OrderStatusEnum.PAID:
            detail = "Paid orders cannot be cancelled. Please request a refund."
        else:
            detail = "Order is already cancelled."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    try:
        order.status = OrderStatusEnum.CANCELLED
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while trying to cancel the order.",
        )
    return MessageResponseSchema(message="Order successfully cancelled.")


@router.post(
    "/refund/{order_id}/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refund Request",
    description="Endpoint for movie refund",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Order successfully refunded."},
        ),
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "payment": "No valid payment found to refund.",
                **STRIPE_ERRORS_EXAMPLES,
            },
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Inactive user.",
            },
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_order_found": "Order with given ID was not found."},
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={
                "not_paid_orders": "Order is not paid.",
                "cancelled": "Cancelled orders cannot be refunded.",
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Database error during refund processing."},
        ),
    },
)
def refund_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    stripe_service: StripeServiceInterface = Depends(get_stripe_service),
) -> MessageResponseSchema:
    """Refund user's order if conditions are met.

    Args:
        order_id: ID of the order to refund.
        current_user: Authenticated user making the request.
        db: Database session.
        stripe_service: Stripe payment service instance.

    Returns:
        Message confirming successful refund.
    """
    order = (
        db.query(OrderModel)
        .filter_by(id=order_id, user_id=current_user.id)
        .with_for_update()
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order with given ID was not found.",
        )

    if order.status != OrderStatusEnum.PAID:
        if order.status == OrderStatusEnum.CANCELLED:
            detail = "Cancelled orders cannot be refunded."
        else:
            detail = "Order is not paid."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    latest_payment = (
        db.query(PaymentModel)
        .filter_by(order_id=order.id)
        .order_by(PaymentModel.created_at.desc())
        .first()
    )

    if not latest_payment or not latest_payment.external_payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid payment found to refund.",
        )

    try:

        stripe_service.create_refund(
            payment_intent_id=latest_payment.external_payment_id
        )

        latest_payment.status = PaymentStatusEnum.REFUNDED
        order.status = OrderStatusEnum.CANCELLED

        movie_ids = [item.movie_id for item in order.order_items]
        db.query(PurchaseModel).filter(
            PurchaseModel.user_id == order.user_id,
            PurchaseModel.movie_id.in_(movie_ids),
        ).delete(synchronize_session=False)

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during refund processing.",
        )
    return MessageResponseSchema(message="Order successfully refunded.")
