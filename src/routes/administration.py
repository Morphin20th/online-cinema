from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status as http_status

from src.database import (
    UserModel,
    ActivationTokenModel,
    OrderModel,
    OrderItemModel,
    OrderStatusEnum,
)
from src.database.session import get_db
from src.dependencies import admin_required
from src.schemas.administration import BaseEmailSchema, ChangeGroupRequest
from src.schemas.common import MessageResponseSchema
from src.schemas.orders import AdminOrderListSchema, AdminOrderSchema
from src.utils import Paginator

router = APIRouter()


def get_user_by_email(email: EmailStr, db: Session):
    return db.query(UserModel).filter(UserModel.email == email).first()


@router.post(
    "/accounts/activate/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(admin_required)],
)
def admin_activate_user(
    data: BaseEmailSchema,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_active:
        return MessageResponseSchema(message="User account is already active")

    try:
        user.is_active = True
        db.query(ActivationTokenModel).filter(
            ActivationTokenModel.user_id == user.id
        ).delete()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating user account",
        )

    return MessageResponseSchema(message="User account activated successfully by admin")


@router.post("/accounts/change-group/", response_model=MessageResponseSchema)
def change_user_group(
    data: ChangeGroupRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_required),
):
    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Prevent changing the group of a user with the same ID as you.",
        )

    if user.group_id == data.group_id:
        return MessageResponseSchema(
            message=f"User already belongs to group {data.group_id}"
        )

    if data.group_id not in [1, 2, 3]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid group ID"
        )

    try:
        user.group_id = data.group_id
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return MessageResponseSchema(
        message=f"User group successfully changed to {data.group_id}."
    )


@router.get(
    "/orders/",
    response_model=AdminOrderListSchema,
    dependencies=[Depends(admin_required)],
)
def get_orders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filter by user id"),
    email: Optional[str] = Query(None, description="Filter by user email"),
    created_at: Optional[str] = Query(
        None, description="Filter by order date (YYYY-MM-DD)"
    ),
    status: Optional[str] = Query(None, description="Filter by order status"),
):
    filters = []
    base_params = {}

    if user_id:
        filters.append(OrderModel.user_id == user_id)
        base_params["user_id"] = user_id

    if created_at:
        try:
            filter_date = datetime.strptime(created_at, "%Y-%m-%d").date()
            filters.append(OrderModel.created_at >= filter_date)
            filters.append(OrderModel.created_at < filter_date + timedelta(days=1))
            base_params["created_at"] = created_at
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

    if status:
        try:
            status_enum = OrderStatusEnum(status.lower())
            filters.append(OrderModel.status == status_enum)
            base_params["status"] = status
        except ValueError:
            allowed_values = [e.value for e in OrderStatusEnum]
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value. Allowed values: {allowed_values}",
            )

    if email:
        filters.append(UserModel.email.ilike(f"%{email}%"))
        base_params["email"] = email

    query = (
        db.query(OrderModel)
        .join(UserModel)
        .options(
            joinedload(OrderModel.order_items).joinedload(OrderItemModel.movie),
            joinedload(OrderModel.user),
        )
        .filter(*filters)
    )

    paginator = Paginator(request, query, page, per_page, base_params)
    orders = paginator.paginate().all()

    try:
        for order in orders:
            if order.total_amount is None:
                order.total_amount = order.total
                db.add(order)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process orders",
        )

    orders_list = [
        AdminOrderSchema(
            user_id=order.user_id,
            email=order.user.email,
            id=order.id,
            status=order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
        )
        for order in orders
    ]

    prev_page, next_page = paginator.get_links()

    return AdminOrderListSchema(
        orders=orders_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
