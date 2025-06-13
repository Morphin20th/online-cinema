from fastapi import HTTPException
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from src.database.models.movies import GenreModel
from src.database.session import get_db
from src.dependencies import get_current_user, moderator_or_admin_required
from src.routes.movies.movies import router
from src.schemas.common import MessageResponseSchema
from src.schemas.movies import GenreSchema, BaseGenreSchema


@router.post(
    "/genres/create/",
    response_model=GenreSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def create_genre(data: BaseGenreSchema, db: Session = Depends(get_db)) -> GenreSchema:
    genre = db.query(GenreModel).filter(GenreModel.name.ilike(data.name)).first()

    if genre:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A genre with name '{data.name}'",
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
    "/genres/{genre_id}/",
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
    "/genres/{genre_id}/",
    response_model=GenreSchema,
    dependencies=[Depends(get_current_user)],
)
def get_genre(genre_id: int, db: Session = Depends(get_db)) -> GenreSchema:
    genre = db.query(GenreModel).filter(GenreModel.id == genre_id).first()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre with the given ID was not found.",
        )
    return GenreSchema.model_validate(genre)


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
