import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, func, Enum, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Integer, DateTime

from ..models.base import Base

if TYPE_CHECKING:
    from ..models.accounts import UserModel
    from ..models.movies import MovieModel


class StatusEnum(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING
    )
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    order_items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order"
    )

    def __repr__(self) -> str:
        return (
            f"<OrderModel(id={self.id}, status={self.status}, "
            f"created_at={self.created_at}, user_id={self.user_id})>"
        )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE")
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE")
    )

    order: Mapped["OrderModel"] = relationship(
        "OrderModel", back_populates="order_items"
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel", back_populates="order_items"
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItemModel(id={self.id}, order_id={self.order_id}, "
            f"movie_id={self.movie_id})>"
        )
