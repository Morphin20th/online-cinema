from __future__ import annotations

import enum
from datetime import datetime, timezone, date, timedelta
from typing import List

from pydantic import EmailStr
from sqlalchemy import (
    Enum,
    String,
    DateTime,
    func,
    ForeignKey,
    Date,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base
from database.utils import generate_secure_token
from security import hash_password, verify_password


class UserGroupEnum(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class GenderEnum(enum.Enum):
    MAN = "man"
    WOMAN = "woman"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum), nullable=False, unique=True
    )

    users: Mapped[List[UserModel]] = relationship("UserModel", back_populates="group")

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False
    )

    group: Mapped[UserGroupModel] = relationship(UserGroupModel, back_populates="users")
    profile: Mapped["UserProfileModel"] = relationship(
        "UserProfileModel", back_populates="user", cascade="all, delete-orphan"
    )
    activation_token: Mapped[ActivationTokenModel] = relationship(
        "ActivationTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_token: Mapped[PasswordResetTokenModel] = relationship(
        "PasswordResetTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[List[RefreshTokenModel]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all"
    )

    def __repr__(self):
        return (
            f"<UserModel(id={self.id}, email={self.email}, is_active={self.is_active})>"
        )

    @property
    def password(self):
        return "Password is write-only."

    @password.setter
    def password(self, new_password: str) -> None:
        self._hashed_password = hash_password(new_password)

    def verify_password(self, new_password: str) -> bool:
        return verify_password(new_password, self._hashed_password)

    @classmethod
    def create(
        cls, email: EmailStr, new_password: str, group_id: Mapped[int]
    ) -> UserModel:
        user = cls(email=email, group_id=group_id)
        user.password = new_password
        return user


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    avatar: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[GenderEnum | None] = mapped_column(Enum(GenderEnum))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    info: Mapped[str | None] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    user: Mapped[UserModel] = relationship("UserModel", back_populates="profile")

    def __repr__(self):
        return (
            f"<UserProfileModel(id={self.id}, first_name={self.first_name}, last_name={self.last_name},"
            f"gender={self.gender}, date_of_birth={self.date_of_birth})>"
        )


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=generate_secure_token
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[UserModel] = relationship(UserModel, back_populates="activation_token")

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<ActivationTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[UserModel] = relationship(
        UserModel, back_populates="password_reset_token"
    )

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<PasswordResetTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False, default=generate_secure_token
    )

    user: Mapped[UserModel] = relationship(UserModel, back_populates="refresh_tokens")

    __table_args__ = (UniqueConstraint("user_id"),)

    def __repr__(self):
        return f"<RefreshTokenModel(id={self.id}, token={self.token}, expires_at={self.expires_at})>"

    @classmethod
    def create(cls, user_id, token, days) -> RefreshTokenModel:
        expires_at = datetime.now(timezone.utc) + timedelta(days=days)
        return cls(user_id=user_id, expires_at=expires_at, token=token)
