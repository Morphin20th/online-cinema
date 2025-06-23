from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.services import StripeService
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
from src.schemas.common import MessageResponseSchema
from src.schemas.orders import BaseOrderSchema
from src.schemas.orders import CreateOrderResponseSchema, MovieSchema, OrderListSchema
from src.utils import Paginator

router = APIRouter()


@router.post("/create/", response_model=CreateOrderResponseSchema)
def create_order(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
) -> CreateOrderResponseSchema:
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
            detail="Error while trying to create an order occurred.",
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


@router.get("/", response_model=OrderListSchema)
def get_orders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderListSchema:
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


@router.post("/cancel/{order_id}/", response_model=MessageResponseSchema)
def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
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
            detail="Error while trying to cancel the order occurred.",
        )
    return MessageResponseSchema(message="Order successfully cancelled.")


@router.post("/refund/{order_id}/", response_model=MessageResponseSchema)
def refund_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    stripe_service: StripeService = Depends(get_stripe_service),
) -> MessageResponseSchema:
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
