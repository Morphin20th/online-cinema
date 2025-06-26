from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.schemas.examples import CURRENT_USER_EXAMPLES
from src.database import (
    UserModel,
    CartModel,
    CartItemModel,
    MovieModel,
    PurchaseModel,
    OrderModel,
    OrderStatusEnum,
    OrderItemModel,
)
from src.database.session import get_db
from src.dependencies import get_current_user
from src.schemas.carts import (
    AddMovieToCartRequestSchema,
    BaseCartSchema,
    CartItemResponseSchema,
)
from src.schemas.common import MessageResponseSchema
from src.utils import aggregate_error_examples

router = APIRouter()


def get_cart_with_items(db: Session, user_id: int) -> BaseCartSchema:
    cart = (
        db.query(CartModel)
        .options(joinedload(CartModel.cart_items).joinedload(CartItemModel.movie))
        .filter(CartModel.user_id == user_id)
        .first()
    )

    if not cart:
        return BaseCartSchema(cart_items=[])
    if not cart.cart_items:
        return BaseCartSchema(cart_items=[])

    cart_items_list = []
    for item in cart.cart_items:
        if item.movie is None:
            continue

        cart_items_list.append(
            CartItemResponseSchema(
                movie_uuid=item.movie.uuid,
                movie_name=item.movie.name,
                cart_id=item.cart_id,
                added_at=item.added_at,
            )
        )

    return BaseCartSchema(cart_items=cart_items_list)


@router.get(
    "/",
    response_model=BaseCartSchema,
    status_code=status.HTTP_200_OK,
    summary="Get User Cart",
    description="Endpoint for getting user cart.",
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
def get_cart(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BaseCartSchema:
    return get_cart_with_items(db, current_user.id)


@router.post(
    "/add/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Add Movie to Cart using UUID",
    description="Endpoint for adding movies to cart by UUID",
    responses={
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "movie_purchased": "Movie already purchased.",
                "movie_in_order": "Movie is currently in the order in the pending status.",
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
            examples={
                "no_movie_found": "Movie with given UUID was not found.",
                "no_cart_found": "Cart not found.",
            },
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict", examples={"movie_in_cart": "Movie already in cart."}
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred during adding movie to a cart."
            },
        ),
    },
)
def add_movie_to_cart(
    data: AddMovieToCartRequestSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageResponseSchema:
    movie = db.query(MovieModel).filter(MovieModel.uuid == data.movie_uuid).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with given UUID was not found.",
        )

    cart = db.query(CartModel).filter(CartModel.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found.",
        )

    already_purchased = (
        db.query(PurchaseModel)
        .filter_by(user_id=current_user.id, movie_id=movie.id)
        .first()
    )
    if already_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already purchased.",
        )

    pending_status = (
        db.query(OrderModel)
        .join(OrderItemModel)
        .filter(
            OrderModel.user_id == current_user.id,
            OrderModel.status == OrderStatusEnum.PENDING,
            OrderItemModel.movie_id == movie.id,
        )
        .first()
    )
    if pending_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is currently in the order in the pending status.",
        )

    exists_in_cart = (
        db.query(CartItemModel).filter_by(cart_id=cart.id, movie_id=movie.id).first()
    )
    if exists_in_cart:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Movie already in cart.",
        )

    try:
        cart_item = CartItemModel(cart_id=cart.id, movie_id=movie.id)
        db.add(cart_item)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during adding movie to a cart.",
        )
    return MessageResponseSchema(message="Movie has been added to cart successfully.")


@router.delete(
    "/items/{movie_uuid}/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Delete Movie from Cart",
    description="Endpoint for removing movie from cart.",
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
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "no_movie_found": "Movie not found in cart.",
                "no_cart_found": "Cart not found.",
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred during removing movie from cart."
            },
        ),
    },
)
def remove_movie_from_cart(
    movie_uuid: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
    cart = db.query(CartModel).filter_by(user_id=current_user.id).first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found.",
        )

    cart_item = (
        db.query(CartItemModel)
        .join(CartItemModel.movie)
        .filter(
            CartItemModel.cart_id == cart.id,
            MovieModel.uuid == movie_uuid,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in cart.",
        )

    try:
        db.delete(cart_item)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during removing movie from cart.",
        )

    return MessageResponseSchema(message="Movie removed from cart.")


@router.delete(
    "/items/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Delete All Movies from Cart",
    description="Endpoint for cleaning shopping cart of movies",
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
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "no_cart_found": "Cart not found.",
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred while removing movies from cart."
            },
        ),
    },
)
def remove_all_movies_from_cart(
    current_user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)
) -> MessageResponseSchema:
    cart = db.query(CartModel).filter_by(user_id=current_user.id).first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found.",
        )

    try:
        for item in cart.cart_items:
            if item.movie is None:
                continue

            db.delete(item)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while removing movies from cart.",
        )
    return MessageResponseSchema(message="All movies removed from cart.")
