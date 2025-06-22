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
    StarModel,
    DirectorModel,
    CartItemModel,
    PurchaseModel,
)
from src.database.session import get_db
from src.dependencies import get_current_user, moderator_or_admin_required
from src.routes.movies import genre_router, star_router
from src.schemas.common import MessageResponseSchema
from src.schemas.movies import (
    CreateMovieRequestSchema,
    MovieDetailSchema,
    UpdateMovieRequestSchema,
    MovieListResponseSchema,
)
from src.utils import Paginator

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
)
def create_movie(
    data: CreateMovieRequestSchema,
    db: Session = Depends(get_db),
) -> MovieDetailSchema:
    existing_movie = (
        db.query(MovieModel)
        .filter(
            MovieModel.name == data.name,
            MovieModel.year == data.year,
            MovieModel.time == data.time,
        )
        .first()
    )
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with name '{data.name}' and release year '{data.year}' "
                f"and duration '{data.time}' already exists."
            ),
        )

    try:
        certification = (
            db.query(CertificationModel)
            .filter(CertificationModel.name.ilike(f"%{data.certification}%"))
            .first()
        )
        if not certification:
            certification = CertificationModel(name=data.certification)
            db.add(certification)
            db.flush()

        genres = []
        for genre_name in data.genres:
            genre = (
                db.query(GenreModel)
                .filter(GenreModel.name.ilike(f"%{genre_name}%"))
                .first()
            )
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.flush()
            genres.append(genre)

        stars = []
        for star_name in data.stars:
            star = (
                db.query(StarModel)
                .filter(StarModel.name.ilike(f"%{star_name}%"))
                .first()
            )
            if not star:
                star = StarModel(name=star_name)
                db.add(star)
                db.flush()
            stars.append(star)

        directors = []
        for director_name in data.directors:
            director = (
                db.query(DirectorModel)
                .filter(DirectorModel.name.ilike(f"%{director_name}%"))
                .first()
            )
            if not director:
                director = DirectorModel(name=director_name)
                db.add(director)
                db.flush()
            directors.append(director)

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
            detail="Something went wrong.",
        )
    return MovieDetailSchema.model_validate(movie)


@router.get(
    "/{movie_uuid}/",
    response_model=MovieDetailSchema,
    dependencies=[Depends(get_current_user)],
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
            detail="Error while removing movie occurred.",
        )

    return MessageResponseSchema(message="Movie deleted successfully")


@router.patch(
    "/{movie_uuid}/",
    response_model=MovieDetailSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def update_movie(
    movie_uuid: UUID,
    movie_data: UpdateMovieRequestSchema,
    db: Session = Depends(get_db),
) -> MovieDetailSchema:
    movie = db.query(MovieModel).filter(MovieModel.uuid == movie_uuid).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    try:
        data_dict = movie_data.model_dump(exclude_unset=True)

        if "certification" in data_dict:
            cert = (
                db.query(CertificationModel)
                .filter(
                    CertificationModel.name.ilike(f"%{data_dict['certification']}%")
                )
                .first()
            )
            if not cert:
                cert = CertificationModel(name=data_dict["certification"])
                db.add(cert)
                db.flush()
            movie.certification = cert
            data_dict.pop("certification")

        if "genres" in data_dict:
            genres_list = []
            for genre_name in data_dict["genres"]:
                genre = (
                    db.query(GenreModel)
                    .filter(GenreModel.name.ilike(f"%{genre_name}%"))
                    .first()
                )

                if not genre:
                    genre = GenreModel(name=genre_name)
                    db.add(genre)
                    db.flush()
                genres_list.append(genre)
            movie.genres = genres_list
            data_dict.pop("genres")

        if "stars" in data_dict:
            stars_list = []
            for star_name in data_dict["stars"]:
                star = (
                    db.query(StarModel)
                    .filter(StarModel.name.ilike(f"%{star_name}%"))
                    .first()
                )

                if not star:
                    star = StarModel(name=star_name)
                    db.add(star)
                    db.flush()
                stars_list.append(star)
            movie.stars = stars_list
            data_dict.pop("stars")

        if "directors" in data_dict:
            directors_list = []
            for director_name in data_dict["directors"]:
                director = (
                    db.query(DirectorModel)
                    .filter(DirectorModel.name.ilike(f"%{director_name}%"))
                    .first()
                )

                if not director:
                    director = DirectorModel(name=director_name)
                    db.add(director)
                    db.flush()
                directors_list.append(director)
            movie.directors = directors_list
            data_dict.pop("directors")

        for key, value in data_dict.items():
            setattr(movie, key, value)
        db.commit()
        db.refresh(movie)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update movie.",
        )

    return MovieDetailSchema.model_validate(movie)


@router.get("/", response_model=MovieListResponseSchema)
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

    paginator = Paginator(request, query, page, per_page, base_params)

    if paginator.total_items == 0:
        return MovieListResponseSchema(
            movies=[], prev_page="", next_page="", total_pages=0, total_items=0
        )

    sortings = parse_sort_params(sort)

    movies = paginator.paginate().order_by(*sortings).all()
    prev_page, next_page = paginator.get_links()

    return MovieListResponseSchema(
        movies=[MovieDetailSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
