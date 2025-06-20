from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime, func, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models.base import Base

if TYPE_CHECKING:
    from ..models.accounts import UserModel
    from ..models.movies import MovieModel


class PurchaseModel(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="purchases")
    movie: Mapped["MovieModel"] = relationship("MovieModel", back_populates="purchases")

    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="unique_user_movie_purchase"),
    )

    def __repr__(self) -> str:
        return (
            f"<PurchaseModel(id={self.id},purchased_at={self.purchased_at}, "
            f"user_id={self.user_id}, movie_id={self.movie_id})>"
        )
