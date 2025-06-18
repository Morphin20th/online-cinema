from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import MovieModel
from src.database.models.accounts import UserModel
from src.database.models.base import Base


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True
    )

    user = relationship(UserModel, back_populates="cart")
    cart_items = relationship("CartItem", back_populates="cart")

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id"), nullable=False
    )

    cart = relationship(Cart, back_populates="cart_items")
    movie = relationship(MovieModel, back_populates="movie")

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="unique_cart_movies_ids"),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem(id={self.id}, added_at={self.added_at}, "
            f"cart_id={self.cart_id}, movie_id={self.movie_id})>"
        )
