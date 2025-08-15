import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    String,
    DECIMAL,
    ForeignKey,
    Table,
    Column,
    UniqueConstraint,
    Integer,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models.base import Base

if TYPE_CHECKING:
    from ..models.carts import CartItemModel
    from ..models.purchases import PurchaseModel
    from ..models.orders import OrderItemModel

MoviesGenresTable = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        Integer,
        ForeignKey(
            "genres.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)

MoviesStarsTable = Table(
    "movies_stars",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "star_id",
        Integer,
        ForeignKey(
            "stars.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)

MoviesDirectorsTable = Table(
    "movies_directors",
    Base.metadata,
    Column(
        "movie_id",
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "director_id",
        Integer,
        ForeignKey(
            "directors.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class GenreModel(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<GenreModel(id={self.id}, name={self.name}>"

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="genres", secondary=MoviesGenresTable
    )


class StarModel(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<StarModel(id={self.id}, name={self.name}>"

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="stars", secondary=MoviesStarsTable
    )


class DirectorModel(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<DirectorModel(id={self.id}, name={self.name}>"

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="directors", secondary=MoviesDirectorsTable
    )


class CertificationModel(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<CertificationModel(id={self.id}, name={self.name}>"

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="certification"
    )


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float | None] = mapped_column(Float)
    gross: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2))
    certification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("certifications.id"), nullable=False
    )

    certification: Mapped["CertificationModel"] = relationship(
        "CertificationModel", back_populates="movies"
    )
    stars: Mapped[list["StarModel"]] = relationship(
        "StarModel", back_populates="movies", secondary=MoviesStarsTable
    )
    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel", back_populates="movies", secondary=MoviesGenresTable
    )
    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel", back_populates="movies", secondary=MoviesDirectorsTable
    )
    cart_items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel", back_populates="movie", cascade="all, delete-orphan"
    )
    purchases: Mapped[List["PurchaseModel"]] = relationship(
        "PurchaseModel", back_populates="movie", cascade="all, delete-orphan"
    )
    order_items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="movie", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="unique_movie_constraint"),
    )

    def __repr__(self) -> str:
        return f"<MovieModel(name={self.name}, year={self.year}, time={self.time})>"
