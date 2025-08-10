from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request, Query, status as http_status
from fastapi.params import Depends
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from src.database import (
    UserModel,
    ActivationTokenModel,
    OrderModel,
    OrderItemModel,
    OrderStatusEnum,
    PaymentModel,
    PaymentStatusEnum,
    PaymentItemModel,
    get_db,
)
from src.dependencies import admin_required
from src.routes.carts import get_cart_with_items
from src.schemas import (
    ADMIN_REQUIRED_EXAMPLES,
    BaseEmailSchema,
    ChangeGroupRequest,
    BaseCartSchema,
    MessageResponseSchema,
    AdminOrderListSchema,
    AdminOrderSchema,
    AdminPaymentsListResponseSchema,
    PaymentListItemSchema,
)
from src.utils import Paginator, aggregate_error_examples

router = APIRouter()


def get_user_by_email(email: EmailStr, db: Session) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()


@router.post(
    "/accounts/activate/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(admin_required)],
    status_code=http_status.HTTP_200_OK,
    summary="User Account Activation by Admin",
    description="Endpoint for activation users by admin",
    responses={
        http_status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={
                "message": "User account activated successfully by admin.",
                "activated": "User account is already active.",
            },
        ),
        http_status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Your account is not activated.",
                **ADMIN_REQUIRED_EXAMPLES,
            },
        ),
        http_status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "no_user_found": "User with given email test@example.com not found."
            },
        ),
        http_status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred during user account activation."
            },
        ),
    },
)
def admin_activate_user(
    data: BaseEmailSchema,
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """Activate a user account by email (admin only).

    Args:
        data: Email of the user to activate.
        db: Database session.

    Returns:
        Success message indicating activation result.
    """

    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"User with given email {data.email} not found.",
        )

    if user.is_active:
        return MessageResponseSchema(message="User account is already active.")

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
            detail="Error occurred during user account activation.",
        )

    return MessageResponseSchema(
        message="User account activated successfully by admin."
    )


@router.post(
    "/accounts/change-group/",
    response_model=MessageResponseSchema,
    status_code=http_status.HTTP_200_OK,
    summary="Change User Group by Admin",
    description="Endpoint for changing user group by admin",
    responses={
        http_status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={
                "message": "User group successfully changed to 1.",
                "has_group": "User already belongs to group 1.",
            },
        ),
        http_status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request", examples={"invalid_group": "Invalid group ID."}
        ),
        http_status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=ADMIN_REQUIRED_EXAMPLES
        ),
        http_status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={
                "inactive_user": "Your account is not activated.",
                "self_group_change": "Prevent changing the group of a user with the same ID as you.",
            },
        ),
        http_status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "no_user_found": "User with given email test@example.com not found."
            },
        ),
        http_status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred during user group changing."},
        ),
    },
)
def change_user_group(
    data: ChangeGroupRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_required),
) -> MessageResponseSchema:
    """Change user group by email (admin only).

    Args:
        data: Email and group ID of the user to change.
        db: Database session.
        current_user: Current authenticated admin user.

    Returns:
        Success message indicating group change result.
    """
    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"User with given email {data.email} not found.",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Prevent changing the group of a user with the same ID as you.",
        )

    if user.group_id == data.group_id:
        return MessageResponseSchema(
            message=f"User already belongs to group {data.group_id}."
        )

    if data.group_id not in [1, 2, 3]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid group ID."
        )

    try:
        user.group_id = data.group_id
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during user group changing.",
        )
    return MessageResponseSchema(
        message=f"User group successfully changed to {data.group_id}."
    )


@router.get(
    "/orders/",
    response_model=AdminOrderListSchema,
    dependencies=[Depends(admin_required)],
    status_code=http_status.HTTP_200_OK,
    summary="Get List of Orders for Admin",
    description="Endpoint for getting the list of all orders available",
    responses={
        http_status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "invalid_date": "Invalid date format. Use YYYY-MM-DD",
                "invalid_status": "Invalid status value. "
                "Allowed values: ['pending', 'paid', 'cancelled']",
            },
        ),
        http_status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=ADMIN_REQUIRED_EXAMPLES
        ),
        http_status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Your account is not activated."},
        ),
        http_status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred during processing of orders."},
        ),
    },
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
) -> AdminOrderListSchema:
    """Get list of all orders (admin only).

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        per_page: Number of items per page.
        db: Database session.
        user_id: Optional filter by user ID.
        email: Optional filter by user email.
        created_at: Optional filter by order date.
        status: Optional filter by order status.

    Returns:
        List of orders with pagination info.
    """

    filters = []
    base_params: Dict[str, Any] = {}

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
            detail="Error occurred during processing of orders.",
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


@router.get(
    "/carts/{user_id}/",
    response_model=BaseCartSchema,
    dependencies=[Depends(admin_required)],
    status_code=http_status.HTTP_200_OK,
    summary="Get User Carts by Admin",
    description="Endpoint for getting user carts for Admin",
    responses={
        http_status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=ADMIN_REQUIRED_EXAMPLES
        ),
        http_status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Your account is not activated."},
        ),
        http_status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_user_found": "User with given ID was not found."},
        ),
    },
)
def get_specific_user_cart(
    user_id: int, db: Session = Depends(get_db)
) -> BaseCartSchema:
    """Get specific user cart (admin only).

    Args:
        user_id: ID of the user whose cart to retrieve.
        db: Database session.

    Returns:
        Cart with items for specified user.
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User with given ID was not found.",
        )

    return get_cart_with_items(db, user_id)


@router.get(
    "/payments/",
    response_model=AdminPaymentsListResponseSchema,
    dependencies=[Depends(admin_required)],
    status_code=http_status.HTTP_200_OK,
    summary="Get List of All Payments available",
    description="Endpoint for getting all available payments by admin",
    responses={
        http_status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "invalid_date": "Invalid date format. Use YYYY-MM-DD",
                "invalid_status": "Invalid status value. "
                "Allowed values: ['successful', 'cancelled', 'refunded']",
            },
        ),
        http_status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=ADMIN_REQUIRED_EXAMPLES
        ),
        http_status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Your account is not activated."},
        ),
    },
)
def get_all_payments(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
    email: Optional[str] = Query(None, description="Filter by user email"),
    created_at: Optional[str] = Query(
        None, description="Filter by payment date (YYYY-MM-DD)"
    ),
    status: Optional[str] = Query(None, description="Filter by payment status"),
) -> AdminPaymentsListResponseSchema:
    """Get list of all payments (admin only).

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        per_page: Number of items per page.
        db: Database session.
        email: Optional filter by user email.
        created_at: Optional filter by payment date.
        status: Optional filter by payment status.

    Returns:
        List of payments with pagination info.
    """
    filters: list = []
    base_params: Dict[str, Any] = {}

    if email:
        filters.append(UserModel.email.ilike(f"%{email}%"))
        base_params["email"] = email

    if created_at:
        try:
            filter_date = datetime.strptime(created_at, "%Y-%m-%d").date()
            filters.append(PaymentModel.created_at >= filter_date)
            filters.append(PaymentModel.created_at < filter_date + timedelta(days=1))
            base_params["created_at"] = created_at
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )

    if status:
        try:
            status_enum = PaymentStatusEnum(status.lower())
            filters.append(PaymentModel.status == status_enum)
            base_params["status"] = status
        except ValueError:
            allowed_values = [e.value for e in PaymentStatusEnum]
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value. Allowed values: {allowed_values}",
            )

    query = (
        db.query(PaymentModel, UserModel.email)
        .join(UserModel, PaymentModel.user_id == UserModel.id)
        .options(
            joinedload(PaymentModel.order).joinedload(OrderModel.order_items),
            joinedload(PaymentModel.payment_items).joinedload(
                PaymentItemModel.order_item
            ),
        )
        .filter(*filters)
        .order_by(PaymentModel.created_at.desc())
    )

    paginator = Paginator(request, query, page, per_page, base_params)
    payments = paginator.paginate().all()

    prev_page, next_page = paginator.get_links()

    payments_list = [
        PaymentListItemSchema(
            created_at=payment.created_at,
            amount=payment.amount,
            status=payment.status,
            email=email,
        )
        for payment, email in payments
    ]

    return AdminPaymentsListResponseSchema(
        payments=payments_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
