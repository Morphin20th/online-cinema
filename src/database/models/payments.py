import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, DECIMAL, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base

if TYPE_CHECKING:
    from ..models.accounts import UserModel
    from ..models.orders import OrderModel, OrderItemModel


class PaymentStatusEnum(enum.Enum):
    SUCCESSFUL = "successfull"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.SUCCESSFUL
    )
    external_payment_id: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="payments")
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="payments")
    payment_items: Mapped[List["PaymentItemModel"]] = relationship(
        "PaymentItemModel", back_populates="payment"
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentModel(id={self.id}, created_at={self.created_at}, amount={self.amount}, "
            f"status={self.status}, user_id={self.user_id}, order_id={self.order_id})>"
        )


class PaymentItemModel(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    price_at_payment: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False
    )

    payment: Mapped["PaymentModel"] = relationship(
        "PaymentModel", back_populates="payment_items"
    )
    order_item: Mapped["OrderItemModel"] = relationship(
        "OrderItemModel", back_populates="payment_items"
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentItemModel(id={self.id}, price_at_payment={self.price_at_payment},"
            f"payment_id={self.payment_id}, order_item_id={self.order_item_id})>"
        )
