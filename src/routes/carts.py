from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.database import UserModel, CartModel, CartItemModel, MovieModel, PurchaseModel
from src.database.session import get_db
from src.dependencies import get_current_user, admin_required
from src.schemas.carts import (
    AddMovieToCartRequestSchema,
    BaseCartSchema,
    CartItemResponseSchema,
)
from src.schemas.common import MessageResponseSchema

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


@router.get("/", response_model=BaseCartSchema)
def get_cart(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BaseCartSchema:
    return get_cart_with_items(db, current_user.id)


@router.post("/add/", response_model=MessageResponseSchema)
def add_movie_to_cart(
    data: AddMovieToCartRequestSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageResponseSchema:
    movie = db.query(MovieModel).filter(MovieModel.uuid == data.movie_uuid).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with given ID was not found.",
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
            detail="Failed to add movie to cart.",
        )
    return MessageResponseSchema(message="Movie has been added to cart successfully.")


@router.delete("/items/{movie_uuid}/", response_model=MessageResponseSchema)
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
            detail="Error while removing movie from cart occurred.",
        )

    return MessageResponseSchema(message="Movie removed from cart.")


@router.get(
    "/{user_id}/", response_model=BaseCartSchema, dependencies=[Depends(admin_required)]
)
def get_specific_user_cart(
    user_id: int, db: Session = Depends(get_db)
) -> BaseCartSchema:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with given ID was not found.",
        )

    return get_cart_with_items(db, user_id)
