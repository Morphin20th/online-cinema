from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.schemas._mixins import YearMixin


class CertificationSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class DirectorSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class StarSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class GenreSchema(BaseModel):
    id: int
    name: str = Field(..., max_length=100)

    model_config = ConfigDict(from_attributes=True)


class BaseMovieSchema(YearMixin, BaseModel):
    name: str = Field(..., max_length=250)
    imdb: float = Field(..., ge=1, le=10)
    description: str
    price: Decimal = Field(..., ge=0)
    certification: CertificationSchema

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseMovieSchema):
    time: int = Field(..., gt=0)
    votes: int = 0
    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]


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


class CreateMovieResponseSchema(BaseMovieSchema):
    id: int
