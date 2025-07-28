import pytest
from sqlalchemy.orm import Session

from src.database import (
    MovieModel,
    CartModel,
    CartItemModel,
    PurchaseModel,
    StarModel,
    GenreModel,
    CertificationModel,
    DirectorModel,
)


def create_genre(db_session: Session, index: int = 0, name="test") -> GenreModel:
    genre = GenreModel(name=f"{name}{index if index != 0 else ''}")
    db_session.add(genre)
    return genre


def create_star(db_session: Session, index: int = 0) -> GenreModel:
    star = StarModel(name=f"star{index}")
    db_session.add(star)
    return star


def create_movie(
    db_session,
    star_fixture,
    certification_fixture,
    director_fixture,
    genre_fixture,
    index: int = 0,
) -> MovieModel:
    movie = MovieModel(
        name=f"Test Movie {index}",
        year=2000 + index,
        time=100 + index,
        imdb=7.0,
        votes=1000 + index,
        description=f"Description {index}",
        price=9.99 + index,
        certification=certification_fixture,
        directors=[director_fixture],
        stars=[star_fixture],
        genres=[genre_fixture],
    )
    db_session.add(movie)
    return movie


@pytest.fixture
def director_fixture(db_session: Session) -> DirectorModel:
    director = DirectorModel(name="director")
    db_session.add(director)
    db_session.commit()
    db_session.refresh(director)
    return director


@pytest.fixture
def certification_fixture(db_session: Session) -> CertificationModel:
    certification = CertificationModel(name="pg-13")
    db_session.add(certification)
    db_session.commit()
    db_session.refresh(certification)
    return certification


@pytest.fixture
def genre_fixture(db_session: Session) -> StarModel:
    genre = create_genre(db_session, name="horror")
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture
def star_fixture(db_session: Session) -> StarModel:
    star = create_star(db_session)
    db_session.commit()
    db_session.refresh(star)
    return star


@pytest.fixture
def stars_fixture(db_session):
    def _create_stars(amount: int):
        stars = [create_star(db_session, index=i) for i in range(amount)]
        db_session.commit()
        for star in stars:
            db_session.refresh(star)
        return stars

    return _create_stars


@pytest.fixture
def genres_fixture(db_session):
    def _create_genres(amount: int):
        genres = [create_genre(db_session, index=i) for i in range(amount)]
        db_session.commit()
        for genre in genres:
            db_session.refresh(genre)
        return genres

    return _create_genres


@pytest.fixture
def movie_fixture(
    db_session, star_fixture, certification_fixture, director_fixture, genre_fixture
) -> MovieModel:

    movie = create_movie(
        db_session,
        star_fixture,
        certification_fixture,
        director_fixture,
        genre_fixture,
    )
    db_session.commit()
    db_session.refresh(movie)
    return movie


@pytest.fixture
def movies_fixture(
    db_session, star_fixture, certification_fixture, director_fixture, genre_fixture
):
    def _create_movies(amount: int):
        movies = [
            create_movie(
                db_session,
                star_fixture,
                certification_fixture,
                director_fixture,
                genre_fixture,
                index=i,
            )
            for i in range(amount)
        ]
        db_session.commit()
        for movie in movies:
            db_session.refresh(movie)
        return movies

    return _create_movies


@pytest.fixture
def cart_fixture(regular_user, db_session) -> CartModel:
    cart = CartModel(user=regular_user)
    db_session.add(cart)
    db_session.commit()
    return cart


@pytest.fixture
def cart_item_fixture(
    regular_user, movie_fixture, db_session, cart_fixture
) -> CartItemModel:
    cart_item = CartItemModel(cart_id=cart_fixture.id, movie_id=movie_fixture.id)
    db_session.add(cart_item)
    db_session.commit()
    return cart_item


@pytest.fixture
def purchased_movie_fixture(regular_user, movie_fixture, db_session) -> PurchaseModel:
    purchased_movie = PurchaseModel(
        user_id=regular_user.id,
        movie_id=movie_fixture.id,
    )
    db_session.add(purchased_movie)
    db_session.commit()
    return purchased_movie
