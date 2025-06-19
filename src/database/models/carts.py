from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models.base import Base

if TYPE_CHECKING:
    from ..models.movies import MovieModel
    from ..models.accounts import UserModel


class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="cart")
    cart_items: Mapped["CartItemModel"] = relationship(
        "CartItemModel", back_populates="cart"
    )

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id})>"


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    cart_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )

    cart: Mapped["CartModel"] = relationship("CartModel", back_populates="cart_items")
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel", back_populates="cart_items"
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id", name="unique_cart_movies_ids"),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem(id={self.id}, added_at={self.added_at}, "
            f"cart_id={self.cart_id}, movie_id={self.movie_id})>"
        )
