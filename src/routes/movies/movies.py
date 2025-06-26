from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.database import (
    MovieModel,
    CertificationModel,
    GenreModel,
    CartItemModel,
    PurchaseModel,
)
from src.database.session import get_db
from src.dependencies import get_current_user, moderator_or_admin_required
from src.routes.movies import genre_router, star_router
from src.routes.movies.movie_utils import (
    get_or_create_certification,
    get_or_create_genres,
    get_or_create_stars,
    get_or_create_directors,
    check_movie_exists,
    get_movie_by_uuid,
    update_movie_relations,
)
from src.schemas.common import MessageResponseSchema
from src.schemas.examples import CURRENT_USER_EXAMPLES, MODERATOR_OR_ADMIN_EXAMPLES
from src.schemas.movies import (
    CreateMovieRequestSchema,
    MovieDetailSchema,
    UpdateMovieRequestSchema,
    MovieListResponseSchema,
)
from src.utils import Paginator, aggregate_error_examples

ALLOWED_SORT_FIELDS = {
    "name": MovieModel.name,
    "year": MovieModel.year,
    "imdb": MovieModel.imdb,
    "price": MovieModel.price,
    "votes": MovieModel.votes,
}

router = APIRouter()
router.include_router(genre_router, prefix="/genres")
router.include_router(star_router, prefix="/stars")


def parse_sort_params(sort_params: Optional[str]) -> list:
    if not sort_params:
        return [desc("name")]

    sort_fields = []
    for part in sort_params.split(","):
        part = part.strip()
        desc_order = part.startswith("-")
        clean_part = part.lstrip("+-")

        column = ALLOWED_SORT_FIELDS.get(clean_part)
        if column:
            sort_fields.append(desc(column) if desc_order else asc(column))

    return sort_fields


@router.post(
    "/create/",
    response_model=MovieDetailSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_201_CREATED,
    summary="Create Movie",
    description="Endpoint for creating movies",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={
                "movie_exists": "A movie with name 'movie name' and release year '2025' "
                "and duration '120' already exists."
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred during movie creation."},
        ),
    },
)
def create_movie(
    data: CreateMovieRequestSchema,
    db: Session = Depends(get_db),
) -> MovieDetailSchema:
    check_movie_exists(db, data.name, data.year, data.time)

    try:
        certification = get_or_create_certification(db, data.certification)
        genres = get_or_create_genres(db, data.genres)
        stars = get_or_create_stars(db, data.stars)
        directors = get_or_create_directors(db, data.directors)

        movie = MovieModel(
            name=data.name,
            year=data.year,
            time=data.time,
            imdb=data.imdb,
            votes=data.votes,
            meta_score=data.meta_score,
            gross=data.gross,
            description=data.description,
            price=data.price,
            certification=certification,
            genres=genres,
            stars=stars,
            directors=directors,
        )

        db.add(movie)
        db.commit()
        db.refresh(movie)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during movie creation.",
        )

    return MovieDetailSchema.model_validate(movie)


@router.patch(
    "/{movie_uuid}/",
    response_model=MovieDetailSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_200_OK,
    summary="Update Movie by UUID",
    description="Endpoint for updating movies",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_movie_found": "Movie with the given ID was not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred while trying to update movie."
            },
        ),
    },
)
def update_movie(
    movie_uuid: UUID,
    movie_data: UpdateMovieRequestSchema,
    db: Session = Depends(get_db),
) -> MovieDetailSchema:
    movie = get_movie_by_uuid(db, movie_uuid)
    data_dict = movie_data.model_dump(exclude_unset=True)

    try:
        data_dict = update_movie_relations(db, movie, data_dict)

        for key, value in data_dict.items():
            setattr(movie, key, value)

        db.commit()
        db.refresh(movie)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while trying to update movie.",
        )

    return MovieDetailSchema.model_validate(movie)


@router.get(
    "/{movie_uuid}/",
    response_model=MovieDetailSchema,
    dependencies=[Depends(get_current_user)],
    status_code=status.HTTP_200_OK,
    summary="Get Movie Details",
    description="Endpoint for getting movie details",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user."},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_movie_found": "Movie with the given ID was not found."},
        ),
    },
)
def get_movie(movie_uuid: UUID, db: Session = Depends(get_db)) -> MovieDetailSchema:
    movie = (
        db.query(MovieModel)
        .options(
            joinedload(MovieModel.genres),
            joinedload(MovieModel.stars),
            joinedload(MovieModel.directors),
        )
        .filter(MovieModel.uuid == movie_uuid)
        .first()
    )

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/{movie_uuid}/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_200_OK,
    summary="Delete Movie by UUID",
    description="Endpoint for deleting movies",
    responses={
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={
                "movie_in_cart": "Movie is in users' carts and cannot be deleted.",
                "movie_purchased": "Movie purchased by some user and cannot be deleted.",
            },
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_movie_found": "Movie with the given ID was not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred while trying to remove movie."
            },
        ),
    },
)
def delete_movie(
    movie_uuid: UUID, db: Session = Depends(get_db)
) -> MessageResponseSchema:
    movie = db.query(MovieModel).filter(MovieModel.uuid == movie_uuid).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    in_cart = db.query(CartItemModel).filter_by(movie_id=movie.id).first()
    if in_cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is in users' carts and cannot be deleted.",
        )

    purchased_by_some_user = (
        db.query(PurchaseModel).filter_by(movie_id=movie.id).first()
    )
    if purchased_by_some_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie purchased by some user and cannot be deleted.",
        )

    try:
        db.delete(movie)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while trying to remove movie.",
        )

    return MessageResponseSchema(message="Movie deleted successfully")


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Movie List",
    description="Endpoint for getting movies",
)
def get_movies(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
    year: Annotated[Optional[int], Query(description="Filter by year")] = None,
    imdb: Annotated[Optional[float], Query(description="Filter by IMDb rate")] = None,
    genre: Annotated[Optional[str], Query(description="Filter by genre")] = None,
    certification: Annotated[
        Optional[str], Query(description="Filter by certification")
    ] = None,
    sort: Optional[str] = Query(None, description="e.g. `-imdb,year`"),
) -> MovieListResponseSchema:
    filters = []
    base_params = {}

    if year:
        filters.append(MovieModel.year == year)
        base_params["year"] = year

    if imdb:
        filters.append(MovieModel.imdb == imdb)
        base_params["imdb"] = imdb

    if genre:
        filters.append(MovieModel.genres.any(GenreModel.name.ilike(f"%{genre}%")))
        base_params["genre"] = genre

    if certification:
        filters.append(
            MovieModel.certification.has(CertificationModel.name.ilike(certification))
        )
        base_params["certification"] = certification

    query = db.query(MovieModel).filter(*filters)

    sortings = parse_sort_params(sort)
    if sortings:
        query = query.order_by(*sortings)
    else:
        query = query.order_by(MovieModel.id.desc())

    paginator = Paginator(request, query, page, per_page, base_params)

    movies = paginator.paginate().all()
    prev_page, next_page = paginator.get_links()

    return MovieListResponseSchema(
        movies=[MovieDetailSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
