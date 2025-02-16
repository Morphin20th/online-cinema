import enum
from datetime import datetime, timezone, date
from typing import List

from sqlalchemy import Enum, String, DateTime, func, ForeignKey, Date, Text, Annotated
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base


class UserGroupEnum(enum.Enum):
    ADMIN = "admin"
    USER = "User"
    MODERATOR = "moderator"


class GenderEnum(enum.Enum):
    MAN = "man"
    WOMAN = "woman"


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[intpk]
    name: Mapped[UserGroupEnum] = mapped_column(nullable=False, unique=True)

    users: Mapped[List["UserModel"]] = relationship("UserModel", back_populates="group")

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), onupdate=func.now(), nullable=False
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )
    group: Mapped[UserGroupModel] = relationship(UserGroupModel, back_populates="users")

    def __repr__(self):
        return (
            f"<UserModel(id={self.id}, email={self.email}, is_active={self.is_active})>"
        )


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[intpk]
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    avatar: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[GenderEnum | None] = mapped_column(Enum(GenderEnum))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    info: Mapped[str | None] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    user: Mapped[UserModel] = relationship(UserModel, back_populates="profile")

    def __repr__(self):
        return (
            f"<UserProfileModel(id={self.id}, first_name={self.first_name}, last_name={self.last_name},"
            f"gender={self.gender}, date_of_birth={self.date_of_birth})>"
        )
