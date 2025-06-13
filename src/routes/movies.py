from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from starlette import status

from src.database.models.movies import (
    MovieModel,
    CertificationModel,
    GenreModel,
    StarModel,
    DirectorModel,
)
from src.database.session import get_db
from src.dependencies import get_current_active_user
from src.dependencies.group import moderator_or_admin_required
from src.schemas.common import MessageResponseSchema
from src.schemas.movies import (
    CreateMovieRequestSchema,
    MovieDetailSchema,
    UpdateMovieRequestSchema,
    MovieListResponseSchema,
    MovieListItem,
)


ALLOWED_SORT_FIELDS = {
    "name": MovieModel.name,
    "year": MovieModel.year,
    "imdb": MovieModel.imdb,
    "price": MovieModel.price,
    "votes": MovieModel.votes,
}

router = APIRouter()


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
            .filter(CertificationModel.name == data.certification)
            .first()
        )
        if not certification:
            certification = CertificationModel(name=data.certification)
            db.add(certification)
            db.flush()

        genres = []
        for genre_name in data.genres:
            genre = db.query(GenreModel).filter(GenreModel.name == genre_name).first()
            if not genre:
                genre = GenreModel(name=genre_name)
                db.add(genre)
                db.flush()
            genres.append(genre)

        stars = []
        for star_name in data.stars:
            star = db.query(StarModel).filter_by(name=star_name).first()
            if not star:
                star = StarModel(name=star_name)
                db.add(star)
                db.flush()
            stars.append(star)

        directors = []
        for director_name in data.directors:
            director = db.query(DirectorModel).filter_by(name=director_name).first()
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
    dependencies=[Depends(get_current_active_user)],
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


# TODO: add purchase condition
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

    db.delete(movie)
    db.commit()

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
                .filter(CertificationModel.name == data_dict["certification"])
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
                    db.query(GenreModel).filter(GenreModel.name == genre_name).first()
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
                star = db.query(StarModel).filter(StarModel.name == star_name).first()

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
                    .filter(DirectorModel.name == director_name)
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
    offset = (page - 1) * per_page

    filters = []

    if year:
        filters.append(MovieModel.year == year)

    if imdb:
        filters.append(MovieModel.imdb == imdb)

    if genre:
        filters.append(MovieModel.genres.any(GenreModel.name.ilike(f"%{genre}%")))

    if certification:
        filters.append(
            MovieModel.certification.has(CertificationModel.name.ilike(certification))
        )

    total_items = db.scalar(
        select(func.count()).select_from(MovieModel).where(*filters)
    )

    if total_items == 0:
        return MovieListResponseSchema(
            movies=[], prev_page="", next_page="", total_pages=0, total_items=0
        )

    sortings = parse_sort_params(sort)

    movies_query = (
        select(MovieModel)
        .where(*filters)
        .offset(offset)
        .order_by(*sortings)
        .limit(per_page)
    )
    movies = db.scalars(movies_query).all()
    total_pages = (total_items + per_page - 1) // per_page

    base_url = str(request.url).split("?")[0]
    next_page = (
        f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else ""
    )
    prev_page = f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else ""

    return MovieListResponseSchema(
        movies=[MovieListItem.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )
