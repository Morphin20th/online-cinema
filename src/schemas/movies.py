from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .common import BaseListSchema
from ._mixins import YearMixin


# --- Models Schemas ---
class BaseGenreSchema(BaseModel):
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class BaseStarSchema(BaseModel):
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class CertificationSchema(BaseModel):
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class DirectorSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class StarSchema(BaseStarSchema):
    id: int


class GenreSchema(BaseGenreSchema):
    id: int


class BaseMovieSchema(YearMixin, BaseModel):
    name: str = Field(..., max_length=250)
    imdb: float = Field(..., ge=1, le=10)
    description: str
    price: Decimal = Field(..., ge=0)
    certification: CertificationSchema

    model_config = ConfigDict(from_attributes=True)


# --- Requests ---
class CreateMovieRequestSchema(YearMixin, BaseModel):
    name: str = Field(..., max_length=250)
    time: int = Field(..., gt=0)
    imdb: float = Field(..., ge=1, le=10)
    votes: int = 0
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    description: str
    price: Decimal = Field(..., ge=0)
    certification: str
    genres: List[str]
    directors: List[str]
    stars: List[str]

    @field_validator("name", "certification", mode="before")
    @classmethod
    def serialize_fields(cls, value: str) -> str:
        return value.lower()


class UpdateMovieRequestSchema(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    certification: Optional[str] = None
    genres: Optional[List[str]] = None
    directors: Optional[List[str]] = None
    stars: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# --- Responses ---
class MovieDetailSchema(BaseMovieSchema):
    uuid: UUID
    time: int = Field(..., gt=0)
    votes: int = 0
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]


class MovieListResponseSchema(BaseListSchema):
    movies: List[MovieDetailSchema]


class GenreListItem(GenreSchema):
    total_movies: int


class GenreListResponseSchema(BaseListSchema):
    genres: List[GenreListItem]


class MoviesByGenreSchema(BaseListSchema):
    id: int
    name: str = Field(..., max_length=100)
    movies: List[BaseMovieSchema]


class StarListResponseSchema(BaseListSchema):
    stars: List[StarSchema]
