from typing import List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database import (
    MovieModel,
    CertificationModel,
    GenreModel,
    StarModel,
    DirectorModel,
)


def get_or_create_certification(
    db: Session, certification_name: str
) -> CertificationModel:
    certification = (
        db.query(CertificationModel)
        .filter(CertificationModel.name.ilike(f"%{certification_name}%"))
        .first()
    )
    if not certification:
        certification = CertificationModel(name=certification_name)
        db.add(certification)
        db.flush()
    return certification


def get_or_create_genres(db: Session, genre_names: List[str]) -> List[GenreModel]:
    genres = []
    for genre_name in genre_names:
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
    return genres


def get_or_create_stars(db: Session, star_names: List[str]) -> List[StarModel]:
    stars = []
    for star_name in star_names:
        star = (
            db.query(StarModel).filter(StarModel.name.ilike(f"%{star_name}%")).first()
        )
        if not star:
            star = StarModel(name=star_name)
            db.add(star)
            db.flush()
        stars.append(star)
    return stars


def get_or_create_directors(
    db: Session, director_names: List[str]
) -> List[DirectorModel]:
    directors = []
    for director_name in director_names:
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
    return directors


def get_movie_by_uuid(db: Session, movie_uuid: UUID) -> MovieModel:
    movie = db.query(MovieModel).filter(MovieModel.uuid == movie_uuid).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


def check_movie_exists(db: Session, name: str, year: int, time: int) -> None:
    existing_movie = (
        db.query(MovieModel)
        .filter(
            MovieModel.name == name,
            MovieModel.year == year,
            MovieModel.time == time,
        )
        .first()
    )
    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"A movie with name '{name}' and release year '{year}' "
                f"and duration '{time}' already exists."
            ),
        )


def update_movie_relations(
    db: Session,
    movie: MovieModel,
    update_data: Dict[str, Any],
    fields_to_process: List[str] = ["certification", "genres", "stars", "directors"],
) -> Dict[str, Any]:
    data_dict = update_data.copy()

    if "certification" in data_dict and "certification" in fields_to_process:
        movie.certification = get_or_create_certification(
            db, data_dict["certification"]
        )
        data_dict.pop("certification")

    if "genres" in data_dict and "genres" in fields_to_process:
        movie.genres = get_or_create_genres(db, data_dict["genres"])
        data_dict.pop("genres")

    if "stars" in data_dict and "stars" in fields_to_process:
        movie.stars = get_or_create_stars(db, data_dict["stars"])
        data_dict.pop("stars")

    if "directors" in data_dict and "directors" in fields_to_process:
        movie.directors = get_or_create_directors(db, data_dict["directors"])
        data_dict.pop("directors")

    return data_dict
