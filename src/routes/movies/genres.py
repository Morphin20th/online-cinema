from fastapi import HTTPException, Request, Query, APIRouter
from fastapi.params import Depends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from src.database import GenreModel, MovieModel
from src.database.session import get_db
from src.dependencies import get_current_user, moderator_or_admin_required
from src.schemas.common import MessageResponseSchema
from src.schemas.movies import (
    GenreSchema,
    BaseGenreSchema,
    GenreListResponseSchema,
    GenreListItem,
    MoviesByGenreSchema,
    MovieDetailSchema,
)
from src.utils import Paginator

router = APIRouter()


@router.post(
    "/create/",
    response_model=GenreSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def create_genre(data: BaseGenreSchema, db: Session = Depends(get_db)) -> GenreSchema:
    genre = db.query(GenreModel).filter(GenreModel.name.ilike(data.name)).first()

    if genre:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A genre with name '{data.name}' already exists.",
        )

    try:
        genre = GenreModel(name=data.name)
        db.add(genre)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return GenreSchema.model_validate(genre)


@router.patch(
    "/{genre_id}/",
    response_model=GenreSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def update_genre(
    genre_id: int, genre_data: BaseGenreSchema, db: Session = Depends(get_db)
) -> GenreSchema:
    genre = db.query(GenreModel).filter(GenreModel.id == genre_id).first()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre with the given ID was not found.",
        )

    try:
        genre.name = genre_data.name
        db.commit()
        db.refresh(genre)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return GenreSchema.model_validate(genre)


@router.get(
    "/{genre_id}/",
    response_model=MoviesByGenreSchema,
    dependencies=[Depends(get_current_user)],
)
def get_movies_by_genre(
    genre_id: int,
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
) -> MoviesByGenreSchema:
    genre = db.query(GenreModel).filter(GenreModel.id == genre_id).first()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre with the given ID was not found.",
        )

    query = (
        db.query(MovieModel).join(MovieModel.genres).filter(GenreModel.id == genre_id)
    )

    paginator = Paginator(request, query, page, per_page)
    movies = paginator.paginate().all()

    prev_page, next_page = paginator.get_links()

    return MoviesByGenreSchema(
        id=genre.id,
        name=genre.name,
        movies=[MovieDetailSchema.model_validate(movie) for movie in movies],
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )


@router.delete(
    "/genres/{genre_id}/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def delete_genre(genre_id: int, db: Session = Depends(get_db)) -> MessageResponseSchema:
    genre = db.query(GenreModel).filter(GenreModel.id == genre_id).first()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre with the given ID was not found.",
        )

    db.delete(genre)
    db.commit()

    return MessageResponseSchema(message="Genre deleted successfully")


@router.get("/", response_model=GenreListResponseSchema)
def get_genres(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(GenreModel, func.count(MovieModel.id).label("total_movies"))
        .outerjoin(MovieModel, GenreModel.movies)
        .group_by(GenreModel.id)
        .order_by(GenreModel.name)
    )

    paginator = Paginator(request, query, page, per_page)
    genres = paginator.paginate().all()
    prev_page, next_page = paginator.get_links()

    genres_list = [
        GenreListItem(id=genre.id, name=genre.name, total_movies=total_movies or 0)
        for genre, total_movies in genres
    ]

    return GenreListResponseSchema(
        genres=genres_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
