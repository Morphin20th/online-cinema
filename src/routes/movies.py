from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from src.database.models.movies import (
    MovieModel,
    CertificationModel,
    GenreModel,
    StarModel,
    DirectorModel,
)
from src.database.session import get_db
from src.dependencies.group import moderator_or_admin_required
from src.schemas.movies import CreateMovieRequestSchema, CreateMovieResponseSchema

router = APIRouter()


@router.post(
    "/create/",
    response_model=CreateMovieResponseSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def create_movie(
    data: CreateMovieRequestSchema,
    db: Session = Depends(get_db),
) -> CreateMovieResponseSchema:
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
    return CreateMovieResponseSchema.model_validate(movie)
