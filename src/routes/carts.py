from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.database import UserModel, CartModel, CartItemModel, MovieModel, PurchaseModel
from src.dependencies import get_current_user
from src.database.session import get_db
from src.schemas.carts import (
    AddMovieToCartRequestSchema,
    BaseCartSchema,
    CartItemResponseSchema,
)
from src.schemas.common import MessageResponseSchema

router = APIRouter()


@router.get("/", response_model=BaseCartSchema)
def get_cart(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BaseCartSchema:
    cart = (
        db.query(CartModel)
        .options(joinedload(CartModel.cart_items))
        .filter(CartModel.user_id == current_user.id)
        .first()
    )

    if not cart:
        return BaseCartSchema(cart_items=[])

    return BaseCartSchema(
        cart_items=[
            CartItemResponseSchema.model_validate(item) for item in cart.cart_items
        ]
    )


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
